# BlockList Dashboard Test Instructions

## Test the Fixed BlockList Dashboard

### 1. Access the Dashboard
- Open browser and go to: `http://127.0.0.1:8000/mb-admin/login/`
- Login with staff credentials:
  - Username: `staff`
  - Password: `staff123`

### 2. Navigate to BlockList
- After login, go to: `http://127.0.0.1:8000/mb-admin/blocklist/`
- You should see the BlockList dashboard with:
  - Statistics cards showing numbers
  - Table with 4 test entries
  - Search functionality
  - Add/Edit buttons working

### 3. Test Data Visible
You should see these test entries:
1. Phone: +8801234567890 (Fraud Detection)
2. IP: 192.168.1.100 (Spam/Abuse)  
3. Phone: +8801999888777 (Fake Orders)

### 4. Test Functionality
- Search for a phone number
- Try adding a new entry
- Test bulk operations
- Check if statistics update

### 5. Django Admin Access
- Go to: `http://127.0.0.1:8000/admin/`
- Login with same credentials
- Look for "Block List Entries" under Dashboard section

## Expected Results
✅ Dashboard loads without JavaScript errors
✅ API calls return data successfully  
✅ Statistics show correct counts
✅ CRUD operations work properly
✅ Bulk operations function correctly

## If Issues Persist
Check browser console for any remaining JavaScript errors and verify:
1. User is logged in and has staff permissions
2. API endpoints are accessible
3. CSRF tokens are properly included