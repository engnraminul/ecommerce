# Dashboard Permissions - Backup Tab Addition

## Summary
Added "Backups" tab option to the Dashboard Permissions list, allowing administrators to grant specific users access to the backup functionality.

## Changes Made

### 1. Updated Dashboard Permissions Model
**File:** `users/models.py`
- Added `('backups', 'Backups')` to the `DASHBOARD_TABS` list in the `DashboardPermission` model
- This change allows the backup tab to appear in the user permissions interface

### 2. Verification
- The backup tab now appears in the dashboard permissions selection UI
- Users can be granted specific access to the backup functionality
- The change integrates with the existing permission system that already checks for `'backups'` access in the dashboard navigation

## Impact

### Before
- Backup tab permissions were not available in the user management interface
- Only superusers could access backups (hardcoded permissions)

### After  
- Administrators can now grant backup access to specific users through the dashboard permissions interface
- Non-superuser staff members can be given selective access to backup functionality
- The permission system is consistent across all dashboard tabs

## Usage

To grant backup access to a user:

1. Go to **Dashboard → Users**
2. Edit a user or create a new user
3. In the **Dashboard Permissions** section, check the **Backups** option
4. Save the user

The user will now see the Backups menu item in the dashboard navigation and can access backup functionality.

## Technical Notes

- No database migration was required as this only updates the choices list
- The dashboard navigation (`dashboard/templates/dashboard/base.html`) already includes the proper permission check: `user|has_dashboard_access:'backups'`
- The backup app already has proper URL routing and views in place
- This change maintains backward compatibility with existing permission configurations