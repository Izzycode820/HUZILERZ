"""
Template Data Binding Service
Converts workspace data to template-ready variables and handles real-time updates
Follows 4 principles: Scalable, Secure, Maintainable, Best Practices
"""
import re
import json
from typing import Dict, Any, List, Optional, Union
from django.template import Template, Context
from django.apps import apps
from django.core.exceptions import ValidationError
from workspace.core.services.base_data_export_service import workspace_data_export_service
import logging

logger = logging.getLogger('workspace.sync.template_binding')


class TemplateDataBindingService:
    """
    Service for binding workspace data to template variables
    Handles both static generation and real-time updates
    """

    # Template variable pattern: {{variable_name}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    # Reserved template variables that cannot be overridden
    RESERVED_VARIABLES = {
        '_metadata', '_site', '_template_data', '_workspace_id', '_timestamp'
    }

    def __init__(self):
        self.variable_cache = {}  # Cache for frequently accessed variables

    def bind_workspace_data_to_template(
        self,
        workspace_id: str,
        template_config: Dict[str, Any],
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bind workspace data to template configuration

        Args:
            workspace_id: UUID of the workspace
            template_config: Template configuration with variables
            template_type: Optional template type for filtering

        Returns:
            Template configuration with bound data
        """
        try:
            # Get workspace data for templates
            workspace_data = workspace_data_export_service.export_for_template(
                workspace_id, template_type
            )

            # Process template configuration recursively
            bound_config = self._process_template_structure(
                template_config, workspace_data
            )

            # Add binding metadata
            bound_config['_binding_metadata'] = {
                'workspace_id': workspace_id,
                'template_type': template_type,
                'bound_at': timezone.now().isoformat(),
                'variables_bound': self._count_variables_bound(template_config),
                'binding_version': '1.0'
            }

            logger.info(f"Successfully bound workspace data to template for workspace {workspace_id}")
            return bound_config

        except Exception as e:
            logger.error(f"Failed to bind workspace data to template: {str(e)}")
            raise ValidationError(f"Template binding failed: {str(e)}")

    def _process_template_structure(
        self,
        structure: Union[Dict, List, str, Any],
        workspace_data: Dict[str, Any]
    ) -> Union[Dict, List, str, Any]:
        """
        Recursively process template structure to bind variables

        Args:
            structure: Template structure (dict, list, string, or other)
            workspace_data: Workspace data for variable replacement

        Returns:
            Processed structure with bound variables
        """
        if isinstance(structure, dict):
            return {
                key: self._process_template_structure(value, workspace_data)
                for key, value in structure.items()
            }

        elif isinstance(structure, list):
            return [
                self._process_template_structure(item, workspace_data)
                for item in structure
            ]

        elif isinstance(structure, str):
            return self._bind_string_variables(structure, workspace_data)

        else:
            # Return as-is for other types (int, bool, None, etc.)
            return structure

    def _bind_string_variables(self, template_string: str, workspace_data: Dict[str, Any]) -> str:
        """
        Replace template variables in a string with workspace data

        Args:
            template_string: String containing template variables
            workspace_data: Workspace data for replacement

        Returns:
            String with variables replaced
        """
        try:
            # Find all template variables in the string
            variables = self.VARIABLE_PATTERN.findall(template_string)

            if not variables:
                return template_string

            result = template_string

            for variable in variables:
                variable = variable.strip()

                # Skip reserved variables
                if variable in self.RESERVED_VARIABLES:
                    continue

                # Get variable value from workspace data
                value = self._resolve_variable_path(variable, workspace_data)

                # Replace variable in result string
                if value is not None:
                    placeholder = f"{{{{{variable}}}}}"

                    # Convert value to string if it's not already
                    if isinstance(value, (dict, list)):
                        # For complex types, use JSON representation
                        value_str = json.dumps(value)
                    elif isinstance(value, bool):
                        # Convert boolean to lowercase string
                        value_str = str(value).lower()
                    else:
                        value_str = str(value)

                    result = result.replace(placeholder, value_str)

            return result

        except Exception as e:
            logger.warning(f"Failed to bind variables in string '{template_string[:50]}...': {str(e)}")
            return template_string  # Return original string on error

    def _resolve_variable_path(self, variable_path: str, workspace_data: Dict[str, Any]) -> Any:
        """
        Resolve dotted variable path to value from workspace data

        Args:
            variable_path: Dotted path like 'business_name' or 'featured_products.0.name'
            workspace_data: Workspace data dictionary

        Returns:
            Resolved value or None if not found
        """
        try:
            # Split path into components
            path_components = variable_path.split('.')
            current_value = workspace_data

            # Navigate through the path
            for component in path_components:
                if isinstance(current_value, dict):
                    current_value = current_value.get(component)
                elif isinstance(current_value, list):
                    try:
                        # Handle array indices
                        index = int(component)
                        if 0 <= index < len(current_value):
                            current_value = current_value[index]
                        else:
                            return None
                    except ValueError:
                        # Component is not a valid index
                        return None
                else:
                    # Cannot navigate further
                    return None

                # If we get None at any point, stop navigation
                if current_value is None:
                    return None

            return current_value

        except Exception as e:
            logger.warning(f"Failed to resolve variable path '{variable_path}': {str(e)}")
            return None

    def _count_variables_bound(self, template_config: Dict[str, Any]) -> int:
        """
        Count total number of template variables in configuration
        """
        def count_in_structure(structure):
            count = 0
            if isinstance(structure, dict):
                for value in structure.values():
                    count += count_in_structure(value)
            elif isinstance(structure, list):
                for item in structure:
                    count += count_in_structure(item)
            elif isinstance(structure, str):
                count += len(self.VARIABLE_PATTERN.findall(structure))
            return count

        return count_in_structure(template_config)

    def generate_static_site_from_template(
        self,
        workspace_id: str,
        template_config: Dict[str, Any],
        output_format: str = 'html'
    ) -> Dict[str, Any]:
        """
        Generate static site files from template configuration with bound data

        Args:
            workspace_id: UUID of the workspace
            template_config: Template configuration
            output_format: Output format ('html', 'json', 'markdown')

        Returns:
            Generated static site files
        """
        try:
            # Bind workspace data to template
            bound_config = self.bind_workspace_data_to_template(
                workspace_id, template_config
            )

            # Generate files based on output format
            if output_format == 'html':
                return self._generate_html_files(bound_config)
            elif output_format == 'json':
                return self._generate_json_files(bound_config)
            elif output_format == 'markdown':
                return self._generate_markdown_files(bound_config)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

        except Exception as e:
            logger.error(f"Failed to generate static site: {str(e)}")
            raise

    def _generate_html_files(self, bound_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate HTML files from bound configuration
        """
        files = {}

        # Generate main HTML file
        html_content = self._render_html_template(bound_config)
        files['index.html'] = html_content

        # Generate additional pages if configured
        if 'pages' in bound_config:
            for page_config in bound_config['pages']:
                page_name = page_config.get('name', 'page')
                page_content = self._render_html_template(page_config)
                files[f'{page_name}.html'] = page_content

        return files

    def _generate_json_files(self, bound_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate JSON files from bound configuration
        """
        files = {}

        # Main data file
        files['data.json'] = json.dumps(bound_config, indent=2, default=str)

        # Separate files for different data types
        if 'featured_products' in bound_config:
            files['products.json'] = json.dumps(
                bound_config['featured_products'], indent=2, default=str
            )

        if 'recent_posts' in bound_config:
            files['posts.json'] = json.dumps(
                bound_config['recent_posts'], indent=2, default=str
            )

        if 'featured_services' in bound_config:
            files['services.json'] = json.dumps(
                bound_config['featured_services'], indent=2, default=str
            )

        return files

    def _generate_markdown_files(self, bound_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate Markdown files from bound configuration
        """
        files = {}

        # Generate README with workspace information
        readme_content = self._generate_readme_content(bound_config)
        files['README.md'] = readme_content

        # Generate individual markdown files for content
        if 'recent_posts' in bound_config:
            for i, post in enumerate(bound_config['recent_posts']):
                filename = f"post-{i+1}-{post.get('title', 'untitled')[:20]}.md"
                filename = re.sub(r'[^\w\-.]', '-', filename.lower())
                files[filename] = self._post_to_markdown(post)

        return files

    def _render_html_template(self, config: Dict[str, Any]) -> str:
        """
        Render HTML template from configuration
        """
        # Basic HTML template structure
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ business_name|default:"Website" }}</title>
    <meta name="description" content="{{ business_description|default:"" }}">
</head>
<body>
    <header>
        <h1>{{ business_name|default:"My Business" }}</h1>
        {% if business_description %}
        <p>{{ business_description }}</p>
        {% endif %}
    </header>

    <main>
        {% if featured_products %}
        <section class="products">
            <h2>Our Products</h2>
            {% for product in featured_products %}
            <div class="product">
                <h3>{{ product.name }}</h3>
                <p>{{ product.description }}</p>
                <p class="price">${{ product.price }}</p>
            </div>
            {% endfor %}
        </section>
        {% endif %}

        {% if recent_posts %}
        <section class="blog">
            <h2>Latest Posts</h2>
            {% for post in recent_posts %}
            <article>
                <h3>{{ post.title }}</h3>
                <p>{{ post.excerpt }}</p>
                <time>{{ post.published_date }}</time>
            </article>
            {% endfor %}
        </section>
        {% endif %}

        {% if featured_services %}
        <section class="services">
            <h2>Our Services</h2>
            {% for service in featured_services %}
            <div class="service">
                <h3>{{ service.name }}</h3>
                <p>{{ service.description }}</p>
                <p class="price">${{ service.price }}</p>
                <p class="duration">{{ service.duration }}</p>
            </div>
            {% endfor %}
        </section>
        {% endif %}
    </main>

    <footer>
        {% if contact_email or contact_phone %}
        <div class="contact">
            {% if contact_email %}<p>Email: {{ contact_email }}</p>{% endif %}
            {% if contact_phone %}<p>Phone: {{ contact_phone }}</p>{% endif %}
        </div>
        {% endif %}
    </footer>
</body>
</html>
        """

        try:
            template = Template(html_template)
            context = Context(config)
            return template.render(context)
        except Exception as e:
            logger.error(f"Failed to render HTML template: {str(e)}")
            # Return basic HTML on error
            return f"""
<!DOCTYPE html>
<html>
<head><title>{config.get('business_name', 'Website')}</title></head>
<body>
    <h1>{config.get('business_name', 'My Business')}</h1>
    <p>Website content will be available soon.</p>
</body>
</html>
            """

    def _generate_readme_content(self, bound_config: Dict[str, Any]) -> str:
        """
        Generate README.md content from bound configuration
        """
        business_name = bound_config.get('business_name', 'My Business')
        description = bound_config.get('business_description', '')

        readme = f"""# {business_name}

{description}

## About This Website

This website was generated using the Huzilerz platform.

"""

        # Add sections based on workspace type
        template_data = bound_config.get('template_data', {})
        workspace_type = template_data.get('workspace_type', 'unknown')

        if workspace_type == 'store':
            readme += """## Products

This is an e-commerce website showcasing our products and services.

"""
        elif workspace_type == 'blog':
            readme += """## Blog

This is a blog website featuring our latest posts and articles.

"""
        elif workspace_type == 'services':
            readme += """## Services

This is a service-based website where you can book appointments and learn about our offerings.

"""

        # Add contact information if available
        contact_email = bound_config.get('contact_email')
        contact_phone = bound_config.get('contact_phone')

        if contact_email or contact_phone:
            readme += "## Contact\n\n"
            if contact_email:
                readme += f"Email: {contact_email}\n\n"
            if contact_phone:
                readme += f"Phone: {contact_phone}\n\n"

        return readme

    def _post_to_markdown(self, post: Dict[str, Any]) -> str:
        """
        Convert post data to Markdown format
        """
        title = post.get('title', 'Untitled')
        content = post.get('content', '')
        published_date = post.get('published_date', '')

        markdown = f"""# {title}

*Published: {published_date}*

{content}
"""
        return markdown

    def update_deployed_site_data(
        self,
        site_id: str,
        workspace_id: str,
        changed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update deployed site with changed workspace data

        Args:
            site_id: ID of the deployed site
            workspace_id: ID of the workspace
            changed_data: Data that has changed

        Returns:
            Update result
        """
        try:
            # Get current site configuration
            DeployedSite = apps.get_model('hosting', 'DeployedSite')
            site = DeployedSite.objects.get(id=site_id)

            # Get updated workspace data
            workspace_data = workspace_data_export_service.export_for_template(
                workspace_id
            )

            # Re-bind template with updated data
            updated_config = self.bind_workspace_data_to_template(
                workspace_id, site.template_config
            )

            # Update site record
            site.template_config = updated_config
            site.save(update_fields=['template_config', 'updated_at'])

            logger.info(f"Updated deployed site {site_id} with new workspace data")

            return {
                'success': True,
                'site_id': site_id,
                'updated_at': site.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to update deployed site data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_template_variables(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template configuration for proper variable usage

        Args:
            template_config: Template configuration to validate

        Returns:
            Validation result with any issues found
        """
        issues = []
        variables_found = set()

        def scan_structure(structure, path=""):
            if isinstance(structure, dict):
                for key, value in structure.items():
                    scan_structure(value, f"{path}.{key}" if path else key)
            elif isinstance(structure, list):
                for i, item in enumerate(structure):
                    scan_structure(item, f"{path}[{i}]")
            elif isinstance(structure, str):
                # Find variables in string
                variables = self.VARIABLE_PATTERN.findall(structure)
                for var in variables:
                    var = var.strip()
                    variables_found.add(var)

                    # Check for reserved variables
                    if var in self.RESERVED_VARIABLES:
                        issues.append({
                            'type': 'reserved_variable',
                            'variable': var,
                            'location': path,
                            'message': f"Variable '{var}' is reserved and cannot be used"
                        })

        # Scan the entire configuration
        scan_structure(template_config)

        return {
            'valid': len(issues) == 0,
            'variables_found': sorted(list(variables_found)),
            'issues': issues,
            'total_variables': len(variables_found)
        }


# Singleton instance for global use
template_binding_service = TemplateDataBindingService()