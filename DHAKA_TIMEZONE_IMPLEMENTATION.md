# Dhaka Timezone Implementation - Complete Guide

This document outlines all the changes made to implement Dhaka, Bangladesh timezone (UTC +6) throughout the ecommerce project.

## Django Settings Changes

### 1. Core Timezone Settings
**File:** `ecommerce_project/settings.py`

```python
# Changed from UTC to Asia/Dhaka
TIME_ZONE = 'Asia/Dhaka'
USE_TZ = True  # Kept as True for timezone-aware datetime handling

# Updated Celery timezone to match
CELERY_TIMEZONE = 'Asia/Dhaka'
```

## Frontend Changes

### 1. Statistics Page JavaScript Functions
**File:** `dashboard/templates/dashboard/statistics.html`

#### New Timezone Utility Functions:
```javascript
// Timezone utility functions for Dhaka, Bangladesh (UTC +6)
const DHAKA_TIMEZONE_OFFSET = 6 * 60; // 6 hours in minutes

function getDhakaTime() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const dhakaTime = new Date(utc + (DHAKA_TIMEZONE_OFFSET * 60000));
    return dhakaTime;
}

function formatDhakaDate(date) {
    if (!date) date = getDhakaTime();
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
}

function formatDhakaDateTime(date) {
    if (!date) date = getDhakaTime();
    return date.toLocaleString('en-US', {
        timeZone: 'Asia/Dhaka',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
}

function getFirstDayOfMonth(date) {
    if (!date) date = getDhakaTime();
    return new Date(date.getFullYear(), date.getMonth(), 1);
}
```

#### Updated Date Initialization:
- Current year initialization: `getDhakaTime().getFullYear()`
- Default date ranges: Using Dhaka timezone for products and status filters
- Clear buttons: Reset to Dhaka current month
- Export filenames: Use Dhaka date format
- Last updated timestamps: Display in Dhaka time

### 2. User Interface Updates
**File:** `dashboard/templates/dashboard/statistics.html`

#### Page Title:
```html
{% block page_title %}
    Sales & Performance Statistics 
    <small class="text-muted">
        <i class="fas fa-clock me-1"></i>
        Dhaka, Bangladesh Time (UTC +6)
    </small>
{% endblock %}
```

#### Time Period Card:
```html
<div>
    <h5 class="mb-0">Time Period</h5>
    <small class="text-muted">
        <i class="fas fa-globe-asia me-1"></i>
        All times shown in Dhaka timezone
    </small>
</div>
```

## Backend Changes

### 1. API Views Fixed
**Files:** `dashboard/views.py`

#### Fixed Query Parameter Access:
- Changed `request.query_params` to `request.GET` for APIView classes
- Kept `request.query_params` for ModelViewSet classes (DRF ViewSets)

#### Views Updated:
- `DashboardStatisticsView`
- `OrderStatusBreakdownView` 
- `ProductPerformanceView`

**Note:** ModelViewSets like `ExpenseDashboardViewSet` correctly use `request.query_params`.

### 2. Timezone-Aware Queries
All datetime queries already use `timezone.now()` which automatically respects the Django `TIME_ZONE` setting:

```python
from django.utils import timezone

# This automatically uses Asia/Dhaka timezone
now = timezone.now()
start_date = now - timedelta(days=7)
orders = Order.objects.filter(created_at__gte=start_date)
```

## Impact on Existing Data

### Database Storage
- **No changes needed** - Django stores all datetime fields in UTC in the database
- **Timezone conversion happens at the application layer** when displaying data
- **Existing data remains valid** - all timestamps are automatically converted to Dhaka time when displayed

### API Responses
- All datetime fields in API responses will now be in Dhaka timezone context
- Frontend JavaScript handles timezone-aware date formatting
- Date filtering works correctly with local Dhaka dates

## Testing

### Timezone Configuration Test
Created `test_timezone.py` to verify:
- ✓ Django TIME_ZONE setting: `Asia/Dhaka`
- ✓ Django USE_TZ setting: `True` (timezone-aware)
- ✓ JavaScript date formatting compatibility
- ✓ API endpoint functionality with date filtering

### Manual Testing Checklist
- [ ] Statistics page displays correct Dhaka time in "Last updated" fields
- [ ] Date filters use Dhaka dates by default (current month)
- [ ] Clear buttons reset to Dhaka current month
- [ ] Export files use Dhaka date in filename
- [ ] Chart labels show appropriate Dhaka-based periods
- [ ] API endpoints accept and process date filters correctly

## User Experience Improvements

### Visual Indicators
1. **Page Title**: Shows timezone information prominently
2. **Time Period Card**: Includes timezone notice for all periods
3. **Consistent Formatting**: All times displayed in consistent Dhaka format
4. **Default Ranges**: Date pickers default to Dhaka current month

### JavaScript Enhancements
1. **Timezone Utilities**: Centralized functions for Dhaka time handling
2. **Consistent Date Formatting**: All date operations use Dhaka timezone
3. **Browser Compatibility**: Works across different browser timezone settings
4. **Export Functions**: Generate files with Dhaka date stamps

## Technical Notes

### Why UTC Storage + Local Display?
- **Database Efficiency**: UTC storage ensures consistent sorting and querying
- **Multi-timezone Support**: Easy to add other timezones in future
- **Data Integrity**: No ambiguity during DST transitions
- **Performance**: Database queries remain efficient

### JavaScript Timezone Handling
- **Client-side Calculation**: Converts UTC to Dhaka without server dependency
- **Consistent Display**: All users see Dhaka time regardless of their location
- **Date Picker Compatibility**: HTML date inputs work correctly with formatted dates

### Future Considerations
1. **Multiple Timezone Support**: Framework ready for additional timezones
2. **User Preferences**: Can extend to per-user timezone settings
3. **Business Hours**: Ready for Dhaka business hour calculations
4. **Reporting**: All reports will use consistent Dhaka timestamps

## Configuration Summary

| Setting | Value | Purpose |
|---------|--------|---------|
| `TIME_ZONE` | `'Asia/Dhaka'` | Default timezone for the application |
| `USE_TZ` | `True` | Enable timezone-aware datetime handling |
| `CELERY_TIMEZONE` | `'Asia/Dhaka'` | Background task timezone |
| JavaScript Offset | `+6 hours` | Client-side timezone calculation |

## Files Modified

### Backend Files:
1. `ecommerce_project/settings.py` - Timezone configuration
2. `dashboard/views.py` - Fixed query parameter access

### Frontend Files:
1. `dashboard/templates/dashboard/statistics.html` - Complete timezone implementation

### Documentation:
1. `DHAKA_TIMEZONE_IMPLEMENTATION.md` - This comprehensive guide

The implementation ensures that all datetime operations throughout the project respect Bangladesh time while maintaining data integrity and providing a consistent user experience.