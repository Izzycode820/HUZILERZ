● Here are the default operations for a typical Shopify e-commerce
  storefront:

  Core Product Operations

  1. getProducts - List products with pagination/filters
  2. getProduct - Single product details with variants
  3. getProductRecommendations - Related/similar products
  4. searchProducts - Product search with filters

  Collection/Category Operations

  5. getCollections - List all collections
  6. getCollection - Single collection with products
  7. getCollectionByHandle - Collection by slug/handle

  Cart Operations

  8. createCart - Create new cart session
  9. getCart - Retrieve cart with items
  10. addToCart - Add item to cart (with variants)
  11. updateCartItem - Change item quantity
  12. removeFromCart - Remove item from cart
  13. applyDiscountCode - Apply promo code <<----- this is the only one left

  Checkout & Order Operations

  14. createCheckout - Start checkout process
  15. getCheckout - Retrieve checkout details
  16. updateCheckout - Update shipping/billing info
  17. completeCheckout - Finalize order
  18. getOrder - Retrieve order details
  19. getCustomerOrders - Customer order history

  Customer Operations

  20. customerCreate - Register customer
  21. customerLogin - Customer login
  22. customerUpdate - Update customer profile
  23. customerRecover - Password reset
  24. customerAddressCreate - Add address
  25. customerAddressUpdate - Update address

  Search & Navigation

  26. search - Global search across products/collections
  27. getMenu - Navigation menu items
  28. getPage - Static pages (About, Contact, etc.)

  Store Operations

  29. getShop - Store information (name, currency, etc.)
  30. getShopPolicies - Return/Privacy policies

  Additional Shopify Features

  31. getBlogPosts - Blog content
  32. getArticles - Blog articles
  33. getMetafields - Custom fields
  34. getProductReviews - Customer reviews
  35. createProductReview - Submit review

  Ready to examine your backend files and start implementing the ones that       
  align with your admin store management!