from django.db import models

# -------------------------------
# SCRAPED MARKET DATA
# -------------------------------

class MarketItem(models.Model):
    title = models.CharField(max_length=255)
    exclude_keywords = models.JSONField(blank=True, null=True, help_text="List of keywords to ignore when scraping/creating listings")

    def __str__(self):
        return self.title


class CompetitorListing(models.Model):
    COMPETITOR_CHOICES = [
        ("CeX", "CeX"),
        ("CashConverters", "CashConverters"),
        ("CashGenerator", "CashGenerator"),
        ("eBay", "eBay"),
    ]

    market_item = models.ForeignKey(MarketItem, on_delete=models.CASCADE, related_name="listings")
    competitor = models.CharField(max_length=50, choices=COMPETITOR_CHOICES)
    title = models.CharField(max_length=255)  # raw listing title
    price = models.FloatField()
    url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now=True)
    store_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.competitor} - {self.title} (£{self.price})"


# -------------------------------
# SHOP INVENTORY
# -------------------------------

class Category(models.Model):
    name = models.CharField(max_length=100)
    attributes = models.JSONField(blank=True, null=True)  # flexible category-specific metadata

    def __str__(self):
        return self.name

class PawnShopAgreement(models.Model):
    agreement_number = models.CharField(max_length=50, unique=True)
    created_date = models.DateField()
    expiry_date = models.DateField()
    previous_agreements = models.TextField(blank=True, null=True)#
    description = models.TextField(blank=True, null=True)
    created_by = models.CharField(max_length=100)
    customer = models.CharField(max_length=255)
    days_gone_past_expiry = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"Agreement {self.agreement_number} - {self.customer}"


class InventoryItem(models.Model):
    STATUS_CHOICES = [
        ("buyback_storage", "Buyback Storage"),
        ("free_stock", "Free Stock"),
        ("sold", "Sold"),
        ("reserved", "Reserved"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_items")
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="buyback_storage")
    buyback_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    final_listing_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    agreement = models.ForeignKey(
        PawnShopAgreement,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        blank=True,
        null=True
    )

    market_item = models.ForeignKey(
        MarketItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_items"
    )


    def __str__(self):
        return f"{self.title} ({self.status})"


class PriceAnalysis(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="price_analyses")
    reasoning = models.TextField()
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2)
    confidence = models.PositiveIntegerField(default=0)  # 0-100%
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.item.title} - £{self.suggested_price}"

# -- Web listing
class WebListing(models.Model):
    inventory_item = models.ForeignKey(
        InventoryItem,
        on_delete=models.CASCADE,
        related_name="web_listings"
    )
    listed_by = models.CharField(max_length=255)  # store username or staff name
    first_uploaded_at = models.DateTimeField(auto_now_add=True)  # time first uploaded
    last_updated_at = models.DateTimeField(auto_now=True)        # auto updates whenever record changes
    update_count = models.PositiveIntegerField(default=0)       # number of times listing was changed
    epos_listing_url = models.URLField(blank=True, null=True)   # optional link to the EPOS listing
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("active", "Active"),
            ("ended", "Ended"),
            ("removed", "Removed")
        ],
        default="active"
    )

    def __str__(self):
        return f"{self.inventory_item.title} listed by {self.listed_by} (£{self.final_price})"
