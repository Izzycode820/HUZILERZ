# Service Management System - Mental Model

> **Document Purpose**: This is a comprehensive design document for extending HUZILERZ from a pure e-commerce platform to a unified **E-commerce + Service Management SaaS**. Use this as the blueprint for future implementation.

---

## Executive Summary

HUZILERZ will support three core business types:
1. **Physical Products** (e-commerce) - Already implemented
2. **Digital Products** (downloads, licenses) - Future implementation
3. **Services** (appointments, bookings, rentals) - Future implementation

This document covers the **Services** mental model in detail.

---

## Part 1: What is a "Service" in Our System?

A **Service** is any offering that is not a tangible product. Instead of shipping an item, the customer receives:
- Access to time with a person (consultation, haircut, massage)
- Access to a resource (meeting room, equipment, vehicle)
- Participation in an event (class, workshop, tour)

### Service Categories

| Category | Examples | Key Characteristics |
|----------|----------|---------------------|
| **1:1 Appointments** | Haircuts, consultations, medical checkups, tutoring | Single customer, single staff, fixed duration |
| **Group Classes/Sessions** | Yoga, workshops, cooking classes, tours | Multiple customers, capacity limit, fixed time |
| **Resource Rentals** | Meeting rooms, cameras, vehicles, venues | No staff required, availability-based, duration varies |
| **Table/Space Reservations** | Restaurant tables, coworking desks, spa rooms | Capacity-based, time slots, location-specific |

---

## Part 2: The Service Model Architecture

### Core Models Needed

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVICE (Main Entity)                        │
├─────────────────────────────────────────────────────────────────────┤
│ id, workspace, name, slug, description                               │
│ service_type: appointment | group_session | resource_rental          │
│ duration_minutes: 30, 60, 90, etc.                                  │
│ capacity: 1 (for 1:1), N (for groups)                               │
│ price, compare_at_price                                              │
│ payment_type: upfront | partial_deposit | pay_on_arrival            │
│ deposit_amount (if partial)                                          │
│ requires_staff: boolean                                              │
│ location_type: physical | virtual | customer_location               │
│ advance_booking_days: how far ahead customers can book               │
│ min_notice_hours: minimum time before appointment                    │
│ buffer_minutes: padding between bookings                             │
│ cancellation_policy: flexible | moderate | strict                    │
│ is_active, status                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐     ┌─────────────────────────────┐
│      STAFF MEMBER           │     │       RESOURCE              │
├─────────────────────────────┤     ├─────────────────────────────┤
│ id, workspace, name, email  │     │ id, workspace, name         │
│ phone, profile_image        │     │ resource_type: room |       │
│ bio, specialties            │     │   equipment | vehicle       │
│ services (M2M)              │     │ location, description       │
│ is_active                   │     │ services (M2M)              │
└─────────────────────────────┘     │ is_active                   │
              │                     └─────────────────────────────┘
              ▼                                   │
┌─────────────────────────────┐                   │
│     STAFF AVAILABILITY      │                   │
├─────────────────────────────┤                   │
│ staff (FK)                  │                   │
│ day_of_week: 0-6            │                   │
│ start_time, end_time        │                   │
│ is_available: boolean       │                   │
│ specific_date (override)    │                   │
└─────────────────────────────┘                   │
                                                  │
                    ┌─────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           BOOKING                                    │
├─────────────────────────────────────────────────────────────────────┤
│ id, workspace                                                        │
│ service (FK)                                                         │
│ customer (FK to Customer)                                            │
│ staff (FK, nullable - for appointments)                              │
│ resource (FK, nullable - for rentals)                                │
│ start_datetime, end_datetime                                         │
│ status: pending | confirmed | completed | cancelled | no_show        │
│ payment_status: unpaid | deposit_paid | fully_paid | refunded       │
│ order (FK to Order - links to payment)                               │
│ participants_count (for group sessions)                              │
│ customer_notes, staff_notes                                          │
│ cancellation_reason                                                  │
│ reminder_sent: boolean                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Payment Types for Services

Services have unique payment requirements compared to products:

### Payment Type Options

| Payment Type | When to Use | How It Works |
|--------------|-------------|--------------|
| **`upfront`** | Classes, fixed-price consultations | Full payment at booking time |
| **`partial_deposit`** | High-value services, rentals | Deposit now, remainder on arrival/completion |
| **`pay_on_arrival`** | Walk-in friendly, trust-based | No payment at booking, pay when service starts |
| **`pay_after`** | Hourly services, variable scope | Pay after service completion (riskier) |

### Payment Flow Examples

```
UPFRONT PAYMENT:
Customer books → Pay full amount → Booking confirmed → Service delivered

PARTIAL DEPOSIT:
Customer books → Pay deposit (e.g., 30%) → Booking confirmed → Pay remainder on arrival

PAY ON ARRIVAL:
Customer books → Booking confirmed (no payment) → Pay when arriving → Service delivered
```

### Refund & Cancellation Logic

| Cancellation Policy | Refund Rules |
|---------------------|--------------|
| **Flexible** | Full refund if cancelled 24+ hours before |
| **Moderate** | 50% refund if cancelled 48+ hours before |
| **Strict** | No refund, only reschedule allowed |

---

## Part 4: Merchant Dashboard - Services Section

### Service List View (Admin Panel)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  SERVICES                                                    [+ Add Service]│
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🏷️ Haircut & Styling                                               │   │
│  │ Type: 1:1 Appointment  |  Duration: 45 min  |  Price: 5,000 XAF    │   │
│  │ Payment: Upfront  |  Staff: 3 assigned  |  Status: ● Active        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🧘 Morning Yoga Class                                               │   │
│  │ Type: Group Session  |  Duration: 60 min  |  Price: 3,000 XAF      │   │
│  │ Payment: Upfront  |  Capacity: 15  |  Status: ● Active             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 📷 Camera Equipment Rental                                          │   │
│  │ Type: Resource Rental  |  Duration: Daily  |  Price: 25,000 XAF/day│   │
│  │ Payment: Deposit (50%)  |  Resources: 5 available  |  Status: ● Active│ │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🍽️ Table Reservation                                                │   │
│  │ Type: Space Booking  |  Duration: 2 hours  |  Price: Free          │   │
│  │ Payment: Pay on Arrival  |  Tables: 12  |  Status: ● Active        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Service Card Data Fields

Each service card should display:
- **Name** + icon based on type
- **Service Type** (Appointment, Group, Rental, Space)
- **Duration** (minutes, hours, or daily)
- **Price** (or "Free" for unpaid reservations)
- **Payment Type** (Upfront, Deposit %, Pay on Arrival)
- **Capacity/Staff/Resources** count
- **Status** (Active/Inactive/Draft)

---

## Part 5: Implementation Strategy

### Phase 1: Models & Database (Foundation)

1. Create `Service` model (extends or relates to Product where `product_type='service'`)
2. Create `StaffMember` model with workspace scoping
3. Create `StaffAvailability` model for working hours
4. Create `Resource` model for rentable items/spaces
5. Create `Booking` model with all status tracking
6. Add migrations

### Phase 2: Service Management (Admin)

1. GraphQL mutations for service CRUD
2. Staff management (add/edit/remove staff, assign services)
3. Availability management (set working hours, block dates)
4. Resource management (add equipment, rooms, vehicles)

### Phase 3: Booking Engine (Customer-Facing)

1. Availability calculator (find open slots based on staff/resource schedules)
2. Booking creation flow
3. Payment integration (deposits, full payments)
4. Email/SMS confirmations
5. Calendar widget for storefronts

### Phase 4: Operations (Post-Booking)

1. Booking dashboard for merchants
2. Reschedule/cancel flows
3. Reminder system (24h before, 1h before)
4. No-show tracking
5. Review/feedback collection

---

## Part 6: Key Service Logic Functions

### Availability Calculation

```python
def get_available_slots(service_id, date, staff_id=None):
    """
    Calculate available time slots for a service on a given date.
    
    Logic:
    1. Get service duration and buffer time
    2. Get all staff who can perform this service (if requires_staff)
    3. For each staff, get their availability for this day
    4. Subtract existing bookings from available windows
    5. Return list of open slots
    
    Returns: [
        {"time": "09:00", "staff_id": "xxx", "available": True},
        {"time": "09:30", "staff_id": "xxx", "available": False},
        ...
    ]
    """
    pass
```

### Booking Creation

```python
def create_booking(service_id, customer_id, slot_datetime, staff_id=None, resource_id=None):
    """
    Create a new booking with payment handling.
    
    Logic:
    1. Verify slot is still available (locking to prevent race conditions)
    2. Create booking record with status='pending'
    3. If payment_type='upfront' or 'partial_deposit':
       - Create Order linked to booking
       - Process payment
       - On success: booking.status='confirmed'
       - On failure: delete booking, return error
    4. If payment_type='pay_on_arrival':
       - booking.status='confirmed' immediately
    5. Send confirmation email/SMS
    6. Schedule reminder notifications
    """
    pass
```

---

## Part 7: Integration with Existing System

### How Services Fit with Products

Option A: **Service extends Product** (Recommended)
- `product_type = 'service'` triggers service-specific behavior
- Reuse existing price, category, workspace scoping
- Service model adds service-specific fields via OneToOne or additional table

Option B: **Service is completely separate**
- Separate model, separate admin section
- More flexibility but more duplication

### How Bookings Fit with Orders

- Each `Booking` can link to an `Order` for payment tracking
- Order items can be of type `product` or `booking`
- This allows mixed carts (buy product + book service together)

---

## Part 8: Cameroon-Specific Considerations

### Payment Methods
- Mobile Money (MTN MoMo, Orange Money) works well for deposits
- Cash on arrival is common for local services
- Support for payment_type='pay_on_arrival' is essential

### Scheduling
- Consider local holidays and market days
- Support French + English in booking confirmations
- SMS is more reliable than email for reminders

### Pricing
- Prices in XAF (no decimals typically needed)
- Consider group discounts for classes
- Allow variable pricing per staff member (senior vs junior stylist)

---

## Part 9: Future Enhancements

- [ ] Recurring bookings (weekly yoga class subscription)
- [ ] Waitlist for fully booked slots
- [ ] Multi-service packages (spa day = massage + facial + sauna)
- [ ] Staff commission tracking
- [ ] Google Calendar / iCal sync
- [ ] Online meeting integration (Zoom, Google Meet) for virtual services
- [ ] Customer booking history and loyalty points

---

## Appendix: Database Field Reference

### Service Fields
| Field | Type | Description |
|-------|------|-------------|
| `service_type` | enum | `appointment`, `group_session`, `resource_rental` |
| `duration_minutes` | int | Length of service |
| `capacity` | int | Max participants (1 for 1:1) |
| `payment_type` | enum | `upfront`, `partial_deposit`, `pay_on_arrival` |
| `deposit_percentage` | decimal | If partial deposit, what % |
| `requires_staff` | bool | Does this need a staff member? |
| `location_type` | enum | `physical`, `virtual`, `customer_location` |
| `advance_booking_days` | int | Max days ahead to book |
| `min_notice_hours` | int | Minimum hours before booking allowed |
| `buffer_minutes` | int | Gap between appointments |
| `cancellation_policy` | enum | `flexible`, `moderate`, `strict` |

### Booking Status Flow
```
pending → confirmed → completed
                   ↘ cancelled
                   ↘ no_show
```

### Payment Status Flow
```
unpaid → deposit_paid → fully_paid
                     ↘ refunded (partial or full)
```

---

*Document Version: 1.0*
*Created: 2026-01-07*
*For: HUZILERZ E-commerce + Service Management SaaS*
