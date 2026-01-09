Perfect. I’ll give you **(A) exact PostHog setup** and **(B) exact dashboards per plan**, mapped to your **4 cards + 1 graph home**, then **Analytics page**.
This is **merchant → customer analytics**, MVP-safe.

---

## A️⃣ PostHog setup (once, clean)

### 1) Create project

* Create **one PostHog project** (not per merchant)
* Everything is scoped by `store_id` (this is critical)

---

### 2) Backend setup (source of truth)

**Library**

* Node: `posthog-node`

**Init once**

```ts
import { PostHog } from 'posthog-node'

export const posthog = new PostHog(POSTHOG_KEY, {
  host: 'https://app.posthog.com'
})
```

**Analytics service**

```ts
trackStoreEvent(event, storeId, payload) {
  posthog.capture({
    distinctId: storeId, // IMPORTANT
    event,
    properties: {
      store_id: storeId,
      ...payload
    }
  })
}
```

📌 Use `store_id` as `distinctId`
→ PostHog aggregates per store automatically.

---

### 3) Frontend setup (customer actions)

**Library**

* `posthog-js`

**Init**

```js
posthog.init(KEY, {
  autocapture: false,
  capture_pageview: false
})
```

**Customer session**

* Generate `session_id` (cookie / localStorage)
* Attach `store_id + session_id` to every event

```js
posthog.capture('add_to_cart', {
  store_id,
  session_id
})
```

---

## B️⃣ DASHBOARDS (exact, per plan)

---

# 🟢 BASIC (MVP – enabled now)

### HOME SCREEN (4 cards + 1 graph)

#### Card 1: Total Revenue

* Event: `order_completed`
* Property: `sum(order_value)`
* Filter: `store_id = current_store`
* Time: last 30 days

#### Card 2: Total Orders

* Event count: `order_completed`

#### Card 3: Conversion Rate

* Formula:

  ```
  unique(session_id) with order_completed
  ÷
  unique(session_id) with store_page_view
  ```

#### Card 4: Avg Order Value

```
sum(order_value) ÷ count(order_completed)
```

---

### Graph: Revenue Over Time

* Line chart
* Event: `order_completed`
* Metric: `sum(order_value)`
* Group by: day

👉 This is **exactly Shopify-level MVP**

---

### ANALYTICS PAGE (Basic)

Sections:

* Orders table (date, value, payment)
* Payment method split (pie)

  * Group by `payment_method`

---

# 🔵 PRO (build now, gate by plan)

### Funnels (PostHog Funnel Insight)

#### Funnel 1: Sales Funnel

1. `store_page_view`
2. `add_to_cart`
3. `checkout_started`
4. `order_completed`

Filter:

* `store_id = current_store`

👉 Shows drop-offs clearly.

---

### Cards (Pro additions)

#### New vs Returning Customers

* New: `customer_created`
* Returning: `order_completed` without `customer_created`

#### Abandoned Checkout Rate

```
checkout_started
− order_completed
```

---

### Graphs (Pro)

* Cart abandonment over time
* Orders by product (group by `product_id`)

---

# 🟣 ENTERPRISE (future – DO NOT BUILD NOW)

Dashboards you design for later:

* LTV (cohorts)
* City-level performance
* Coupon impact
* Refund rate
* Delivery success rate

You already enabled this by:

* `store_id`
* `session_id`
* clean events

---

## C️⃣ How gating works (important)

You **do not block dashboards** — you block **events**.

Example:

```ts
if (store.plan >= PRO) {
  track('checkout_started')
}
```

So:

* Basic merchants literally **cannot generate Pro data**
* No retroactive confusion
* No fake zeros

---

## D️⃣ What you ship TODAY

✅ 4 cards
✅ 1 revenue graph
✅ Blank analytics page → now populated
✅ Clean upgrade path
✅ Safe free-tier usage

---

## Final truth

* This is **not heavy**
* This is **not overengineering**
* This is **merchant-grade analytics**
* This fits Cameroon reality perfectly

If you want next:

* SQL-style PostHog formulas (copy/paste)
* UX layout for the analytics page
* Or a **plan comparison table** for pricing
