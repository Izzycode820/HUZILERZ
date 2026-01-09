"""
Management command to seed demo workspaces with realistic product data
Theme-agnostic design - reusable for sneakers, fashion, electronics, etc.

Usage:
    # Sneakers theme
    python manage.py seed_demo_data --workspace=sneakers-demo --theme=sneakers --products=100

    # Fashion theme (future)
    python manage.py seed_demo_data --workspace=fashion-demo --theme=fashion --products=150

    # With custom config
    python manage.py seed_demo_data --workspace=sneakers-demo --config=sneakers_config.json

     # Step 2: Create demo workspace
  source myenv/Scripts/activate python manage.py create_demo_workspace      
  --theme=sneakers

  # Step 3: Seed with data
  source myenv/Scripts/activate python manage.py seed_demo_data
  --workspace=sneakers-demo --theme=sneakers --products=100 --images        

  # Or clear and reseed
  source myenv/Scripts/activate python manage.py seed_demo_data
  --workspace=sneakers-demo --theme=sneakers --products=100 --images        
  --clear

  🔄 Reusable for Other Themes

  To create a fashion theme demo later, just add to THEME_CONFIGS in        
  seed_demo_data.py:

  'fashion': {
      'categories': [
          {'name': 'Dresses', 'slug': 'dresses', 'product_count': 30},      
          # ... more categories
      ],
      'product_templates': [
          {'prefix': 'Summer Dress', 'brand': 'Zara', 'price_range':        
  (20000, 50000)},
          # ... more templates
      ]
  }

  Then run: python manage.py seed_demo_data --workspace=fashion-demo        
  --theme=fashion

  Ready to test!
"""

import random
import json
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from workspace.core.models import Workspace
from workspace.store.models import Product, Category, MediaUpload


# THEME CONFIGURATIONS
# Each theme has categories and product templates
THEME_CONFIGS = {
    'sneakers': {
        'categories': [
            {'name': "Men's Sneakers", 'slug': 'mens-sneakers', 'description': 'Premium sneakers for men', 'product_count': 25},
            {'name': "Women's Sneakers", 'slug': 'womens-sneakers', 'description': 'Stylish sneakers for women', 'product_count': 25},
            {'name': "Kids' Sneakers", 'slug': 'kids-sneakers', 'description': 'Fun and comfortable sneakers for kids', 'product_count': 15},
            {'name': 'Running Shoes', 'slug': 'running-shoes', 'description': 'High-performance running shoes', 'product_count': 15},
            {'name': 'Basketball Shoes', 'slug': 'basketball-shoes', 'description': 'Professional basketball footwear', 'product_count': 10},
            {'name': 'Casual Sneakers', 'slug': 'casual-sneakers', 'description': 'Everyday casual sneakers', 'product_count': 10},
            {'name': 'Featured', 'slug': 'featured', 'description': 'Best sellers and featured products', 'product_count': 0, 'is_featured': True},
        ],
        'product_templates': [
            {'prefix': 'Air Max Pro', 'brand': 'Nike', 'price_range': (35000, 65000)},
            {'prefix': 'Ultra Boost', 'brand': 'Adidas', 'price_range': (40000, 70000)},
            {'prefix': 'Classic Runner', 'brand': 'Puma', 'price_range': (25000, 45000)},
            {'prefix': 'Sport Elite', 'brand': 'Reebok', 'price_range': (30000, 55000)},
            {'prefix': 'Street Style', 'brand': 'Vans', 'price_range': (20000, 40000)},
            {'prefix': 'Performance Max', 'brand': 'Nike', 'price_range': (45000, 85000)},
            {'prefix': 'Comfort Plus', 'brand': 'New Balance', 'price_range': (35000, 60000)},
            {'prefix': 'Speed Runner', 'brand': 'Asics', 'price_range': (40000, 75000)},
        ],
        'descriptions': [
            '• Lightweight mesh upper for breathability\n• Air cushioning for maximum comfort\n• Durable rubber outsole\n• Available in multiple colors\n• Perfect for running and casual wear',
            '• Premium leather construction\n• Responsive cushioning technology\n• Enhanced grip and traction\n• Stylish modern design\n• Suitable for all-day wear',
            '• Breathable fabric upper\n• Memory foam insole\n• Shock-absorbing midsole\n• Non-slip rubber outsole\n• Great for sports and everyday use',
            '• Sleek contemporary design\n• High-performance materials\n• Superior arch support\n• Moisture-wicking interior\n• Ideal for active lifestyles',
            '• Classic silhouette\n• Comfortable padded collar\n• Flexible sole construction\n• Easy to clean and maintain\n• Versatile styling options',
        ],
        'colors': ['Black', 'White', 'Red', 'Blue', 'Grey', 'Navy', 'Green', 'Pink', 'Purple', 'Orange'],
        'sizes': ['36', '37', '38', '39', '40', '41', '42', '43', '44', '45'],
    }
}


class Command(BaseCommand):
    help = 'Seed demo workspace with realistic product data (theme-agnostic)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workspace',
            type=str,
            required=True,
            help='Workspace slug to seed (e.g., sneakers-demo)'
        )
        parser.add_argument(
            '--theme',
            type=str,
            default='sneakers',
            help='Theme type (sneakers, fashion, electronics, etc.)'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=100,
            help='Total number of products to create (default: 100)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products and categories before seeding'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to custom JSON config file'
        )
        parser.add_argument(
            '--images',
            action='store_true',
            help='Create MediaUpload records with online image URLs'
        )

    def handle(self, *args, **options):
        workspace_slug = options['workspace']
        theme = options['theme']
        total_products = options['products']
        clear_data = options['clear']
        config_file = options.get('config')
        create_images = options['images']

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Seeding Demo Data')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Workspace: {workspace_slug}')
        self.stdout.write(f'Theme: {theme}')
        self.stdout.write(f'Products: {total_products}')
        self.stdout.write(f'{"="*60}\n')

        try:
            # Get workspace
            workspace = self._get_workspace(workspace_slug)
            self.stdout.write(f'✓ Found workspace: {workspace.name}')

            # Load theme config
            config = self._load_config(theme, config_file)
            self.stdout.write(f'✓ Loaded {theme} theme configuration')

            # Clear existing data if requested
            if clear_data:
                self._clear_existing_data(workspace)
                self.stdout.write(self.style.WARNING('✓ Cleared existing products and categories'))

            # Create categories
            categories = self._create_categories(workspace, config['categories'])
            self.stdout.write(f'✓ Created {len(categories)} categories')

            # Create products
            created_count = self._create_products(
                workspace,
                categories,
                config,
                total_products,
                create_images
            )
            self.stdout.write(f'✓ Created {created_count} products')

            # Summary
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(self.style.SUCCESS('✅ Demo data seeding completed successfully!'))
            self.stdout.write(f'{"="*60}')
            self.stdout.write(f'Workspace: {workspace.name} ({workspace.slug})')
            self.stdout.write(f'Categories: {len(categories)}')
            self.stdout.write(f'Products: {created_count}')
            self.stdout.write(f'{"="*60}\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}\n'))
            raise

    def _get_workspace(self, slug):
        """Get workspace by slug"""
        try:
            workspace = Workspace.objects.get(slug=slug)
            return workspace
        except Workspace.DoesNotExist:
            raise CommandError(
                f'Workspace "{slug}" not found. '
                f'Create it first: python manage.py create_demo_workspace --theme=sneakers'
            )

    def _load_config(self, theme, config_file):
        """Load theme configuration from built-in or custom file"""
        if config_file:
            # Load from custom JSON file
            config_path = Path(config_file)
            if not config_path.exists():
                raise CommandError(f'Config file not found: {config_file}')

            with open(config_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    raise CommandError(f'Invalid JSON in config file: {e}')
        else:
            # Load from built-in theme configs
            if theme not in THEME_CONFIGS:
                raise CommandError(
                    f'Theme "{theme}" not found. Available themes: {", ".join(THEME_CONFIGS.keys())}'
                )
            return THEME_CONFIGS[theme]

    def _clear_existing_data(self, workspace):
        """Clear existing products and categories"""
        Product.objects.filter(workspace=workspace).delete()
        Category.objects.filter(workspace=workspace).delete()
        MediaUpload.objects.filter(workspace=workspace, entity_type='product').delete()
        MediaUpload.objects.filter(workspace=workspace, entity_type='category').delete()

    def _create_categories(self, workspace, category_configs):
        """Create categories from config"""
        categories = {}

        for idx, cat_config in enumerate(category_configs):
            category = Category.objects.create(
                workspace=workspace,
                name=cat_config['name'],
                slug=cat_config.get('slug', ''),  # Auto-generated if not provided
                description=cat_config.get('description', ''),
                is_visible=cat_config.get('is_visible', True),
                is_featured=cat_config.get('is_featured', False),
                sort_order=idx,
            )
            categories[cat_config['slug']] = {
                'object': category,
                'product_count': cat_config.get('product_count', 0),
            }

        return categories

    def _create_products(self, workspace, categories, config, total_products, create_images):
        """Create products and distribute across categories"""
        product_templates = config.get('product_templates', [])
        descriptions = config.get('descriptions', [])
        colors = config.get('colors', ['Black', 'White', 'Red', 'Blue'])

        # Distribute products across categories (excluding featured)
        regular_categories = {
            slug: data for slug, data in categories.items()
            if data['product_count'] > 0
        }

        created_count = 0
        product_number = 1

        for cat_slug, cat_data in regular_categories.items():
            category_obj = cat_data['object']
            products_needed = cat_data['product_count']

            self.stdout.write(f'  Creating {products_needed} products for {category_obj.name}...')

            for i in range(products_needed):
                # Generate product data
                template = random.choice(product_templates)
                description = random.choice(descriptions)
                color = random.choice(colors)

                # Generate realistic price
                min_price, max_price = template['price_range']
                price = Decimal(random.randint(min_price, max_price))

                # 30% chance of sale price
                compare_at_price = None
                if random.random() < 0.3:
                    discount = random.uniform(0.10, 0.25)  # 10-25% off
                    compare_at_price = price / Decimal(1 - discount)
                    compare_at_price = compare_at_price.quantize(Decimal('0.01'))

                # Generate product name
                product_name = f"{template['prefix']} {color} Edition"
                if product_number % 10 == 0:
                    product_name = f"{template['prefix']} Limited {color}"

                # Create product
                product = Product.objects.create(
                    workspace=workspace,
                    name=product_name,
                    description=description,
                    price=price,
                    compare_at_price=compare_at_price,
                    brand=template['brand'],
                    category=category_obj,
                    status='published',
                    published_at=timezone.now(),
                    track_inventory=True,
                    inventory_quantity=random.randint(5, 50),
                    product_type='physical',
                    requires_shipping=True,
                )

                # Create MediaUpload records for product images
                if create_images:
                    self._create_product_images(workspace, product, product_number)

                created_count += 1
                product_number += 1

                # Stop if we've reached total_products
                if created_count >= total_products:
                    break

            if created_count >= total_products:
                break

        # Assign 10 random products to Featured category
        if 'featured' in categories:
            featured_category = categories['featured']['object']
            all_products = list(Product.objects.filter(workspace=workspace))
            featured_products = random.sample(all_products, min(10, len(all_products)))

            for product in featured_products:
                product.category = featured_category
                product.save(update_fields=['category'])

        return created_count

    def _create_product_images(self, workspace, product, product_number):
        """Create MediaUpload records for product images using online sources"""
        # Use picsum.photos for placeholder images (fast and reliable)
        # Different seed per product for variety
        num_images = random.randint(1, 4)  # 1-4 images per product

        for img_num in range(num_images):
            # Generate unique image URL
            seed = (product_number * 1000) + img_num
            image_url = f'https://picsum.photos/800/800?random={seed}'

            MediaUpload.objects.create(
                workspace=workspace,
                uploaded_by=workspace.owner,  # System-generated
                media_type='image',
                entity_type='product',
                entity_id=str(product.id),
                original_filename=f'product_{product_number}_img_{img_num}.jpg',
                file_path=f'demo/products/{product.id}/{img_num}.jpg',  # Virtual path
                file_url=image_url,
                file_size=0,  # Unknown for external URLs
                mime_type='image/jpeg',
                width=800,
                height=800,
                status='completed',
                uploaded_at=timezone.now(),
                processed_at=timezone.now(),
            )
