# Huzilaz Theme Development & Architecture

## 2. Template Development Workflow

### Design Phase (Builder.io)
**Purpose:** Create pixel-perfect UI mockups as design specifications
**Process:**
- Design complete templates in Builder.io
- Export HTML/CSS as reference files
- Use as visual blueprint for React development
- No automated conversion - manual recreation only

### Development Phase (React)
**Purpose:** Build production-ready templates with full functionality
**Process:**
- Recreate Builder.io designs exactly in React components
- Add React hooks, state management, and business logic
- Integrate with workspace APIs (products, cart, orders)
- Configure Puck for safe user customization

### Template Types & Tiers

**FREE Templates:**
- Static catalogs with WhatsApp ordering
- No backend integration required
- Basic contact forms
- CDN-hosted only

**PAID Templates:**
- Full stateful React applications
- Fapshi + MTN Mobile Money integration
- Shopping cart with localStorage/sessionStorage
- Django backend integration
- Order management and tracking

**EXCLUSIVE Templates:**
- Complete frontend applications
- Some inherit Huzilaz backend
- Some have custom backend systems
- High-price sales (100k-200k FCFA)
- Customer showcase websites

### Template Type System

**Template Types = Workspace Types:**
- **E-commerce** → Store workspace data only
- **Services** → Services workspace data only
- **Blog** → Blog workspace data only
- **Restaurant** → Restaurant workspace data only

**Compatibility Validation:**
- Templates declare compatible workspace types
- System validates template-workspace match during deployment
- Prevents mismatches (e-commerce theme with restaurant workspace)

### Component Architecture

**Shared Component Library:**
- Build reusable React components (Button, Card, Header, etc.)
- Templates assemble these components
- Ensures consistency across all templates
- Maintainable and scalable

**Puck Integration:**
- Safe customization boundaries
- Users can only modify visual elements
- Core functionality locked and protected
- Customizations stored in database only

### Development Pipeline

**Local Development:**
1. Design in Builder.io
2. Export HTML/CSS reference
3. Build React components matching design
4. Add state management and hooks
5. Test with workspace APIs
6. Configure Puck editable fields

**Production Deployment:**
1. Build and optimize React components
2. Upload to CDN with versioning
3. Update template metadata in database
4. Make available in theme store

### Template Validation

**Pre-Deployment Checks:**
- Workspace type compatibility
- Required API endpoints available
- Puck configuration valid
- Performance benchmarks met
- Mobile responsiveness verified

**Quality Assurance:**
- Test with real workspace data
- Verify all customization options work
- Ensure no breaking changes to core functionality
- Validate across different devices and browsers

### Version Management

**Update Strategy:**
- Master templates use semantic versioning
- User clones stay on current version unless updated
- Users manually opt-in to new versions
- Customizations preserved during updates
- Theme store shows only latest version

**Change Detection:**
- Git-based version control for development
- CDN version directories for production
- Database tracks all template versions
- Checksums for asset change detection