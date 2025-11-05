from django.contrib import admin
from .models import PricingRule, SeasonalPricing, DemandPricing, PricingHistory

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'priority', 'is_active')
    list_filter = ('rule_type', 'is_active')
    search_fields = ('name', 'description')

@admin.register(SeasonalPricing)
class SeasonalPricingAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'start_date', 'end_date', 'is_active')
    list_filter = ('season', 'is_active')
    search_fields = ('name',)

@admin.register(DemandPricing)
class DemandPricingAdmin(admin.ModelAdmin):
    list_display = ('equipment_type', 'low_demand_threshold', 'high_demand_threshold', 'is_active')
    list_filter = ('is_active',)

@admin.register(PricingHistory)
class PricingHistoryAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'effective_date', 'rate_type', 'adjusted_rate')
    list_filter = ('effective_date', 'rate_type')
    search_fields = ('equipment__name',)
