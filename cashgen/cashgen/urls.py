from django.contrib import admin
from django.urls import path
import pricing.views as v

urlpatterns = [
    path('', v.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('individual-item-analysis/', v.individual_item_analysis_view, name='individual_item_analysis'),
    path('individual-item-analyser/', v.individual_item_analyser_view, name='individual_item_analyser'),
    path('item-buying-analyser/', v.item_buying_analyser_view, name='item_buying_analyser'),
    path("inventory/free/", v.inventory_free_stock_view, name="inventory_free_stock"),
    path('marketitem_suggestions', v.marketitem_suggestions, name='marketitem_suggestions'),
    path('link_inventory_to_marketitem/', v.link_inventory_to_marketitem, name='link_inventory_to_marketitem'),
    path('unlink_inventory_from_marketitem/', v.unlink_inventory_from_marketitem, name='unlink_inventory_from_marketitem'),
    path('launch-playwright-listing/', v.launch_playwright_listing, name='launch_playwright_listing'),
    path('update_marketitem_keywords/', v.update_marketitem_keywords, name='update_marketitem_keywords'),
    path("bulk-analysis", v.bulk_analysis, name='bulk_analysis'),
    path('scan-barcodes/', v.scan_barcodes, name='scan_barcodes'),
    path('bulk-analyse-items/', v.bulk_analyse_items, name='bulk_analyse_items'),
    path("api/price-analysis/<int:analysis_id>/", v.price_analysis_detail, name="price_analysis_detail"),
    path('scrape-nospos/', v.scrape_nospos_view, name='scrape_nospos_view'),
    path('detect_irrelevant_competitors/', v.detect_irrelevant_competitors, name='detect_irrelevant_competitors'),
]
