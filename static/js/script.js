// API base URL
const API_BASE = '/api';

// Application state
let currentUser = null;
let currentPage = 'dashboard';
let editingTaskId = null;
let currentEditReason = '';
let sharingTaskId = null;
let editingServiceId = null;
let currentFilters = {
    date: 'all',
    branch: 'all',
    staff: 'all',
    status: 'all',
    service: 'all'
};

// DOM Elements
const loginPage = document.getElementById('login-page');
const navigation = document.getElementById('navigation');
const dashboardPage = document.getElementById('dashboard-page');
const tasksPage = document.getElementById('tasks-page');
const staffPage = document.getElementById('staff-page');
const reportsPage = document.getElementById('reports-page');
const databasePage = document.getElementById('database-page');

// API functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (response.status === 401) {
            handleLogout();
            return null;
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API call failed:', error);
        showToast('Network error occurred', 'error');
        return null;
    }
}

// Authentication functions
async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const userType = document.querySelector('.user-type.active').getAttribute('data-role');

    const result = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });

    if (result && result.success) {
        currentUser = result.user;
        showApp();
        showToast('Login successful!', 'success');
    } else {
        showToast(result?.message || 'Login failed', 'error');
    }
}

async function handleLogout() {
    await apiCall('/logout', { method: 'POST' });
    currentUser = null;
    showLogin();
    showToast('You have been logged out.', 'warning');
}

async function checkAuth() {
    const result = await apiCall('/current-user');
    if (result && result.user) {
        currentUser = result.user;
        showApp();
    } else {
        showLogin();
    }
}

// Data fetching functions
async function fetchTasks(filters = {}) {
    return await apiCall(`/tasks?${new URLSearchParams(filters)}`);
}

async function fetchServices() {
    return await apiCall('/services');
}

async function fetchUsers() {
    return await apiCall('/users');
}

async function fetchDashboardStats() {
    return await apiCall('/dashboard/stats');
}

async function fetchTopPerformers() {
    return await apiCall('/dashboard/top-performers');
}

async function fetchOverdueTasks() {
    return await apiCall('/dashboard/overdue-tasks');
}

// Data submission functions
async function createTask(taskData) {
    return await apiCall('/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData)
    });
}

async function updateTask(taskId, taskData) {
    return await apiCall(`/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify(taskData)
    });
}

async function deleteTask(taskId) {
    return await apiCall(`/tasks/${taskId}`, {
        method: 'DELETE'
    });
}

async function shareTask(taskId, staffName) {
    return await apiCall(`/tasks/${taskId}/share`, {
        method: 'POST',
        body: JSON.stringify({ staff_name: staffName })
    });
}

async function createService(serviceData) {
    return await apiCall('/services', {
        method: 'POST',
        body: JSON.stringify(serviceData)
    });
}

async function updateService(serviceId, serviceData) {
    return await apiCall(`/services/${serviceId}`, {
        method: 'PUT',
        body: JSON.stringify(serviceData)
    });
}

async function deleteService(serviceId) {
    return await apiCall(`/services/${serviceId}`, {
        method: 'DELETE'
    });
}

// UI Functions
function showLogin() {
    loginPage.classList.remove('hidden');
    navigation.classList.add('hidden');
    dashboardPage.classList.add('hidden');
    tasksPage.classList.add('hidden');
    staffPage.classList.add('hidden');
    reportsPage.classList.add('hidden');
    databasePage.classList.add('hidden');
}

async function showApp() {
    loginPage.classList.add('hidden');
    navigation.classList.remove('hidden');

    // Update UI based on user role
    document.getElementById('userRoleDisplay').textContent =
        `${currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1)} User`;

    // Show/hide admin-only elements
    const staffNav = document.getElementById('staff-nav');
    const reportsNav = document.getElementById('reports-nav');
    const databaseNav = document.getElementById('database-nav');
    const revenueCard = document.getElementById('revenueCard');
    const actionsHeader = document.getElementById('actionsHeader');
    const addStaffBtn = document.getElementById('addStaffBtn');
    const addServiceBtn = document.getElementById('addServiceBtn');

    if (currentUser.role === 'admin') {
        staffNav.classList.remove('hidden');
        reportsNav.classList.remove('hidden');
        databaseNav.classList.remove('hidden');
        revenueCard.classList.remove('hidden');
        actionsHeader.classList.remove('hidden');
        if (addStaffBtn) addStaffBtn.classList.remove('hidden');
        if (addServiceBtn) addServiceBtn.classList.remove('hidden');
    } else if (currentUser.role === 'manager') {
        staffNav.classList.remove('hidden');
        reportsNav.classList.remove('hidden');
        databaseNav.classList.remove('hidden');
        revenueCard.classList.add('hidden');
        actionsHeader.classList.remove('hidden');
        if (addStaffBtn) addStaffBtn.classList.add('hidden');
        if (addServiceBtn) addServiceBtn.classList.remove('hidden');
    } else {
        staffNav.classList.add('hidden');
        reportsNav.classList.add('hidden');
        databaseNav.classList.add('hidden');
        revenueCard.classList.add('hidden');
        actionsHeader.classList.add('hidden');
        if (addStaffBtn) addStaffBtn.classList.add('hidden');
        if (addServiceBtn) addServiceBtn.classList.add('hidden');
    }

    // Load initial data
    await populateStaffDropdown();
    await populateServiceDropdown();
    await populateStaffList();
    await populateServiceDatabase();

    navigateToPage(currentPage);
}

async function navigateToPage(page) {
    // Hide all pages
    dashboardPage.classList.add('hidden');
    tasksPage.classList.add('hidden');
    staffPage.classList.add('hidden');
    reportsPage.classList.add('hidden');
    databasePage.classList.add('hidden');

    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));

    // Show the selected page
    switch(page) {
        case 'dashboard':
            dashboardPage.classList.remove('hidden');
            document.querySelector('[data-page="dashboard"]').classList.add('active');
            await updateDashboard();
            break;
        case 'tasks':
            tasksPage.classList.remove('hidden');
            document.querySelector('[data-page="tasks"]').classList.add('active');
            await renderTasks();
            break;
        case 'staff':
            staffPage.classList.remove('hidden');
            document.querySelector('[data-page="staff"]').classList.add('active');
            await updateStaffAlerts();
            break;
        case 'reports':
            reportsPage.classList.remove('hidden');
            document.querySelector('[data-page="reports"]').classList.add('active');
            await updateReports();
            break;
        case 'database':
            databasePage.classList.remove('hidden');
            document.querySelector('[data-page="database"]').classList.add('active');
            break;
    }

    currentPage = page;
}

// Data population functions
async function populateStaffDropdown() {
    const assignedToSelect = document.getElementById('assignedTo');
    const filterStaff = document.getElementById('filterStaff');

    if (!assignedToSelect || !filterStaff) return;

    assignedToSelect.innerHTML = '<option value="">Assign Staff</option>';
    filterStaff.innerHTML = '<option value="all">All Staff</option>';

    const users = await fetchUsers();
    if (users && !users.error) {
        users.forEach(user => {
            if (user.role === 'staff') {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = user.username;
                assignedToSelect.appendChild(option);

                const filterOption = document.createElement('option');
                filterOption.value = user.username;
                filterOption.textContent = user.username;
                filterStaff.appendChild(filterOption);
            }
        });
    }
}

async function populateServiceDropdown() {
    const serviceTypeSelect = document.getElementById('serviceType');
    const filterService = document.getElementById('filterService');

    if (!serviceTypeSelect || !filterService) return;

    serviceTypeSelect.innerHTML = '<option value="">Select Service</option>';
    filterService.innerHTML = '<option value="all">All Services</option>';

    const services = await fetchServices();
    if (services && !services.error) {
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service.name;
            option.textContent = service.name;
            option.dataset.serviceId = service.id;
            serviceTypeSelect.appendChild(option);

            const filterOption = document.createElement('option');
            filterOption.value = service.name;
            filterOption.textContent = service.name;
            filterService.appendChild(filterOption);
        });
    }
}

async function populateStaffList() {
    const staffListContainer = document.getElementById('staffListContainer');
    if (!staffListContainer) return;

    const users = await fetchUsers();
    if (users && !users.error) {
        staffListContainer.innerHTML = '';
        users.forEach(user => {
            const card = document.createElement('div');
            card.className = 'staff-card';
            card.innerHTML = `
                <div class="staff-avatar">${user.username.charAt(0)}</div>
                <div class="staff-name">${user.username}</div>
                <div class="staff-role">${user.role.charAt(0).toUpperCase() + user.role.slice(1)}</div>
                <div class="staff-email">${user.email}</div>
            `;
            staffListContainer.appendChild(card);
        });
    }
}

async function populateServiceDatabase() {
    const serviceListContainer = document.getElementById('serviceListContainer');
    if (!serviceListContainer) return;

    const services = await fetchServices();
    if (services && !services.error) {
        serviceListContainer.innerHTML = '';
        services.forEach(service => {
            const serviceItem = document.createElement('div');
            serviceItem.className = 'service-item';
            serviceItem.innerHTML = `
                <div><strong>${service.name}</strong></div>
                <div>Price: ₹${service.price} | Fee: ₹${service.fee} | Charge: ₹${service.charge}</div>
                <div>Link: <a href="${service.link}" target="_blank">${service.link}</a></div>
                <div>Note: ${service.note}</div>
                ${currentUser.role !== 'staff' ? `
                <div class="mt-1">
                    <button class="action-btn edit-btn" data-service-id="${service.id}">Edit</button>
                    <button class="action-btn delete-btn" data-service-id="${service.id}">Delete</button>
                </div>
                ` : ''}
            `;

            if (currentUser.role !== 'staff') {
                serviceItem.querySelector('.edit-btn').addEventListener('click', () => editService(service.id));
                serviceItem.querySelector('.delete-btn').addEventListener('click', () => deleteService(service.id));
            }

            serviceListContainer.appendChild(serviceItem);
        });
    }
}

// Task management functions
async function renderTasks() {
    const taskTableBody = document.getElementById('taskTableBody');
    const recentTasksTable = document.getElementById('recentTasksTable');

    if (!taskTableBody || !recentTasksTable) return;

    const tasks = await fetchTasks(currentFilters);
    if (tasks && !tasks.error) {
        // Render tasks table
        taskTableBody.innerHTML = '';
        tasks.forEach(task => {
            const row = createTaskRow(task, true);
            taskTableBody.appendChild(row);
        });

        // Render recent tasks (first 10)
        recentTasksTable.innerHTML = '';
        tasks.slice(0, 10).forEach(task => {
            const row = createTaskRow(task, false);
            recentTasksTable.appendChild(row);
        });
    }
}

function createTaskRow(task, includeActions) {
    const row = document.createElement('tr');

    const taskDate = new Date(task.task_date);
    const formattedDate = taskDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    row.innerHTML = `
        <td>${task.order_no}${task.edited ? '<span class="edit-indicator" title="Edited">✏️</span>' : ''}</td>
        <td>${task.customer_name}</td>
        <td>${task.service_type}</td>
        <td>
            <span class="status status-${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span>
            ${task.shared_with.length > 0 ? '<span title="Shared task"> 🔗</span>' : ''}
        </td>
        <td>${task.assigned_to}</td>
        <td>${formattedDate}</td>
        <td>${task.contact_number}</td>
    `;

    if (includeActions) {
        const actionsCell = document.createElement('td');

        if (currentUser.role === 'admin') {
            actionsCell.innerHTML = `
                <button class="action-btn edit-btn" data-id="${task.id}">Edit</button>
                <button class="action-btn delete-btn" data-id="${task.id}">Delete</button>
                <button class="action-btn share-task-btn" data-id="${task.id}">Share</button>
            `;
        } else if (currentUser.role === 'manager') {
            actionsCell.innerHTML = `
                <button class="action-btn edit-btn" data-id="${task.id}">Edit</button>
                <button class="action-btn share-task-btn" data-id="${task.id}">Share</button>
            `;
        } else {
            actionsCell.innerHTML = `
                <select class="status-select" data-id="${task.id}">
                    <option value="Received" ${task.status === 'Received' ? 'selected' : ''}>Received</option>
                    <option value="Pending" ${task.status === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="In Progress" ${task.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                    <option value="Completed" ${task.status === 'Completed' ? 'selected' : ''}>Completed</option>
                    <option value="Hold" ${task.status === 'Hold' ? 'selected' : ''}>Hold</option>
                    <option value="Cancelled" ${task.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
                <button class="action-btn share-task-btn" data-id="${task.id}">Share</button>
            `;
        }

        row.appendChild(actionsCell);

        // Add event listeners
        if (currentUser.role === 'admin' || currentUser.role === 'manager') {
            actionsCell.querySelector('.edit-btn').addEventListener('click', () => editTask(task.id));
        }

        if (currentUser.role === 'admin') {
            actionsCell.querySelector('.delete-btn').addEventListener('click', () => deleteTask(task.id));
        }

        if (currentUser.role === 'staff') {
            actionsCell.querySelector('.status-select').addEventListener('change', (e) => {
                updateTaskStatus(task.id, e.target.value);
            });
        }

        actionsCell.querySelector('.share-task-btn').addEventListener('click', () => showShareModal(task.id));
    }

    return row;
}

// Dashboard functions
async function updateDashboard() {
    const stats = await fetchDashboardStats();
    if (stats && !stats.error) {
        document.getElementById('totalTasks').textContent = stats.total_tasks;
        document.getElementById('tasksToday').textContent = stats.tasks_today;
        document.getElementById('completedTasks').textContent = stats.completed_tasks;

        if (currentUser.role === 'admin') {
            document.getElementById('totalRevenue').textContent = `₹${stats.total_revenue.toLocaleString()}`;
        }
    }

    await updateWinners();
    await updateOverdueTasks();
    await renderTasks(); // To update recent tasks
}

async function updateWinners() {
    const winnersCards = document.getElementById('winnersCards');
    const winnersContainer = document.getElementById('winnersContainer');

    if (!winnersCards) return;

    const topPerformers = await fetchTopPerformers();
    if (topPerformers && !topPerformers.error && topPerformers.length > 0) {
        winnersContainer.classList.remove('hidden');
        winnersCards.innerHTML = '';

        topPerformers.forEach((winner, index) => {
            const card = document.createElement('div');
            card.className = `winner-card ${index === 0 ? '' : index === 1 ? 'second' : 'third'}`;

            let place = '';
            if (index === 0) place = '🥇';
            else if (index === 1) place = '🥈';
            else place = '🥉';

            card.innerHTML = `
                <h4>${place} ${winner.name}</h4>
                <p>Completed Tasks: <strong>${winner.completed_tasks}</strong></p>
                ${currentUser.role === 'admin' ? `<p>Revenue: <strong>₹${winner.total_revenue.toLocaleString()}</strong></p>` : ''}
                <p>Score: <strong>${Math.round(winner.score)}</strong></p>
            `;
            winnersCards.appendChild(card);
        });
    } else {
        winnersContainer.classList.add('hidden');
    }
}

async function updateOverdueTasks() {
    const overdueTasksTable = document.getElementById('overdueTasksTable');
    const overdueTasksContainer = document.getElementById('overdueTasksContainer');

    if (!overdueTasksTable) return;

    const overdueTasks = await fetchOverdueTasks();
    if (overdueTasks && !overdueTasks.error && overdueTasks.length > 0) {
        overdueTasksContainer.classList.remove('hidden');
        overdueTasksTable.innerHTML = '';

        overdueTasks.forEach(task => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${task.order_no}</td>
                <td>${task.customer_name}</td>
                <td>${task.service_type}</td>
                <td><span class="status status-${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span></td>
                <td>${task.assigned_to}</td>
                <td>${new Date(task.task_date).toLocaleDateString()}</td>
                <td>${task.hours_overdue} hours</td>
            `;
            overdueTasksTable.appendChild(row);
        });
    } else {
        overdueTasksContainer.classList.add('hidden');
    }
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');

    if (!toast || !toastMessage) return;

    toastMessage.textContent = message;
    toast.className = 'toast';

    if (type === 'error') {
        toast.classList.add('error');
        toast.querySelector('i').className = 'fas fa-exclamation-circle';
    } else if (type === 'warning') {
        toast.classList.add('warning');
        toast.querySelector('i').className = 'fas fa-exclamation-triangle';
    } else {
        toast.querySelector('i').className = 'fas fa-check-circle';
    }

    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    setupEventListeners();
});

function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.getAttribute('data-page');
            navigateToPage(page);
        });
    });

    // User type selector
    document.querySelectorAll('.user-type').forEach(selector => {
        selector.addEventListener('click', () => {
            document.querySelectorAll('.user-type').forEach(s => s.classList.remove('active'));
            selector.classList.add('active');
        });
    });

    // Add more event listeners as needed...
}

// Add these placeholder functions for now
async function editTask(taskId) {
    showToast('Edit task functionality coming soon', 'warning');
}

async function updateTaskStatus(taskId, newStatus) {
    showToast('Status update functionality coming soon', 'warning');
}

async function showShareModal(taskId) {
    showToast('Share task functionality coming soon', 'warning');
}

async function editService(serviceId) {
    showToast('Edit service functionality coming soon', 'warning');
}

async function deleteService(serviceId) {
    if (confirm('Are you sure you want to delete this service?')) {
        showToast('Delete service functionality coming soon', 'warning');
    }
}

async function updateStaffAlerts() {
    // Implementation coming soon
}

async function updateReports() {
    // Implementation coming soon
}