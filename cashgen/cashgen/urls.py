"""
URL configuration for cashgen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import pricing.views as v

urlpatterns = [
    path('', v.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('individual-item-analysis/', v.individual_item_analysis_view, name='individual_item_analysis'),
    path('individual-item-analyser/', v.individual_item_analyser_view, name='individual_item_analyser'),
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

]
