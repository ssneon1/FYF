    // Runtime state (populated from backend)
    let tasks = [];

    // Services (populated from backend)
    let serviceDatabase = [];

    // Staff list (try to load from backend; fallback minimal)
    let STAFF_LIST = [];

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
    const staffPanelPage = document.getElementById('staff-panel');
    const userRoleDisplay = document.getElementById('userRoleDisplay');
    const logoutBtn = document.getElementById('logoutBtn');
    const userTypeSelectors = document.querySelectorAll('.user-type');
    const loginForm = document.getElementById('login-form');
    const navLinks = document.querySelectorAll('.nav-link');
    const staffNav = document.getElementById('staff-nav');
    const reportsNav = document.getElementById('reports-nav');
    const databaseNav = document.getElementById('database-nav');
    const revenueCard = document.getElementById('revenueCard');
    const taskFormContainer = document.getElementById('taskFormContainer');
    const taskForm = document.getElementById('taskForm');
    const formTitle = document.getElementById('formTitle');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    const taskTableBody = document.getElementById('taskTableBody');
    const recentTasksTable = document.getElementById('recentTasksTable');
    const taskSearch = document.getElementById('taskSearch');
    const actionsHeader = document.getElementById('actionsHeader');
    const assignedToSelect = document.getElementById('assignedTo');
    const staffListContainer = document.getElementById('staffListContainer');
    const staffPerformanceCards = document.getElementById('staffPerformanceCards');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const editReasonModal = document.getElementById('editReasonModal');
    const closeModal = document.getElementById('closeModal');
    const editReason = document.getElementById('editReason');
    const saveWithReason = document.getElementById('saveWithReason');
    const shareTaskModal = document.getElementById('shareTaskModal');
    const closeShareModal = document.getElementById('closeShareModal');
    const staffListModal = document.getElementById('staffListModal');
    const confirmShare = document.getElementById('confirmShare');
    const addStaffBtn = document.getElementById('addStaffBtn');
    const statusUpdateModal = document.getElementById('statusUpdateModal');
    const closeStatusModal = document.getElementById('closeStatusModal');
    const statusUpdateMessage = document.getElementById('statusUpdateMessage');
    const statusOrderNo = document.getElementById('statusOrderNo');
    const statusNewStatus = document.getElementById('statusNewStatus');
    const closeStatusBtn = document.getElementById('closeStatusBtn');
    const filterDate = document.getElementById('filterDate');
    const customDateContainer = document.getElementById('customDateContainer');
    const customDate = document.getElementById('customDate');
    const filterBranch = document.getElementById('filterBranch');
    const filterStaff = document.getElementById('filterStaff');
    const filterStatus = document.getElementById('filterStatus');
    const filterService = document.getElementById('filterService');
    const applyFilters = document.getElementById('applyFilters');
    const resetFilters = document.getElementById('resetFilters');
    const serviceTypeSelect = document.getElementById('serviceType');
    const serviceTooltip = document.getElementById('serviceTooltip');
    const overdueTasksTable = document.getElementById('overdueTasksTable');
    const overdueTasksContainer = document.getElementById('overdueTasksContainer');
    const winnersCards = document.getElementById('winnersCards');
    const winnersContainer = document.getElementById('winnersContainer');
    const staffAlertsContainer = document.getElementById('staffAlertsContainer');
    const serviceFormContainer = document.getElementById('serviceFormContainer');
    const serviceForm = document.getElementById('serviceForm');
    const serviceFormTitle = document.getElementById('serviceFormTitle');
    const addServiceBtn = document.getElementById('addServiceBtn');
    const submitServiceBtn = document.getElementById('submitServiceBtn');
    const cancelServiceBtn = document.getElementById('cancelServiceBtn');
    const serviceListContainer = document.getElementById('serviceListContainer');
    const serviceSearch = document.getElementById('serviceSearch');

    // Staff Panel Elements
    const currentStaffName = document.getElementById('currentStaffName');
    const staffTotalTasks = document.getElementById('staffTotalTasks');
    const staffPendingTasks = document.getElementById('staffPendingTasks');
    const staffMyTasks = document.getElementById('staffMyTasks');
    const staffExtraTasks = document.getElementById('staffExtraTasks');
    const allTasksContainer = document.getElementById('allTasksContainer');
    const myTasksContainer = document.getElementById('myTasksContainer');
    const extraTasksContainer = document.getElementById('extraTasksContainer');
    const allTasksSearch = document.getElementById('allTasksSearch');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Event Listeners
    document.addEventListener('DOMContentLoaded', initApp);
    
    userTypeSelectors.forEach(selector => {
      selector.addEventListener('click', () => {
        userTypeSelectors.forEach(s => s.classList.remove('active'));
        selector.classList.add('active');
      });
    });
    
    loginForm.addEventListener('submit', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = e.target.getAttribute('data-page');
        navigateToPage(page);
      });
    });
    
    addTaskBtn.addEventListener('click', showTaskForm);
    cancelTaskBtn.addEventListener('click', hideTaskForm);
    taskForm.addEventListener('submit', handleTaskSubmit);
    taskSearch.addEventListener('input', filterTasks);
    
    closeModal.addEventListener('click', () => {
      editReasonModal.style.display = 'none';
    });
    
    saveWithReason.addEventListener('click', saveTaskWithReason);
    
    closeShareModal.addEventListener('click', () => {
      shareTaskModal.style.display = 'none';
    });
    
    confirmShare.addEventListener('click', shareTask);
    
    addStaffBtn.addEventListener('click', showAddStaffForm);
    
    closeStatusModal.addEventListener('click', () => {
      statusUpdateModal.style.display = 'none';
    });
    
    closeStatusBtn.addEventListener('click', () => {
      statusUpdateModal.style.display = 'none';
    });
    
    filterDate.addEventListener('change', () => {
      if (filterDate.value === 'custom') {
        customDateContainer.style.display = 'block';
      } else {
        customDateContainer.style.display = 'none';
      }
    });
    
    applyFilters.addEventListener('click', applyTaskFilters);
    resetFilters.addEventListener('click', resetTaskFilters);
    
    serviceTypeSelect.addEventListener('mouseover', showServiceTooltip);
    serviceTypeSelect.addEventListener('mouseout', hideServiceTooltip);
    serviceTypeSelect.addEventListener('change', updateServiceDetails);
    
    addServiceBtn.addEventListener('click', showServiceForm);
    cancelServiceBtn.addEventListener('click', hideServiceForm);
    serviceForm.addEventListener('submit', handleServiceSubmit);
    serviceSearch.addEventListener('input', filterServices);

    // Staff Panel Event Listeners
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const tabId = button.getAttribute('data-tab');
        switchTab(tabId);
      });
    });

    allTasksSearch.addEventListener('input', filterAllTasks);

    // Initialize the application
    function initApp() {
      // Check if user is already logged in (from session storage)
      const savedUser = sessionStorage.getItem('currentUser');
      if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showApp();
      } else {
        showLogin();
      }
    }

    // Show login page
    function showLogin() {
      loginPage.classList.remove('hidden');
      navigation.classList.add('hidden');
      dashboardPage.classList.add('hidden');
      tasksPage.classList.add('hidden');
      staffPage.classList.add('hidden');
      reportsPage.classList.add('hidden');
      databasePage.classList.add('hidden');
      staffPanelPage.classList.add('hidden');
    }

    // Show main application
    function showApp() {
      loginPage.classList.add('hidden');
      navigation.classList.remove('hidden');
      
      userRoleDisplay.textContent = `${currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1)} User`;
      
      // Show/hide admin-only elements
      if (currentUser.role === 'admin') {
        staffNav.classList.remove('hidden');
        reportsNav.classList.remove('hidden');
        databaseNav.classList.remove('hidden');
        revenueCard.classList.remove('hidden');
        actionsHeader.classList.remove('hidden');
        addStaffBtn.classList.remove('hidden');
        addServiceBtn.classList.remove('hidden');
      } else if (currentUser.role === 'manager') {
        staffNav.classList.remove('hidden');
        reportsNav.classList.remove('hidden');
        databaseNav.classList.remove('hidden');
        revenueCard.classList.add('hidden');
        actionsHeader.classList.remove('hidden');
        addStaffBtn.classList.add('hidden');
        addServiceBtn.classList.remove('hidden');
      } else {
        // Staff user
        staffNav.classList.add('hidden');
        reportsNav.classList.add('hidden');
        databaseNav.classList.add('hidden');
        revenueCard.classList.add('hidden');
        actionsHeader.classList.add('hidden');
        addStaffBtn.classList.add('hidden');
        addServiceBtn.classList.add('hidden');
      }
      
      // Populate staff dropdown
      populateStaffDropdown();
      
      // Populate staff list
      populateStaffList();
      
      // Populate service dropdown
      populateServiceDropdown();
      
      // Populate service database
      populateServiceDatabase();
      
      // Populate filter dropdowns
      populateFilterDropdowns();
      
      navigateToPage(currentPage);
      // Load latest data from backend
      fetchTasksAndRender();
      loadServicesFromBackend();
      updateDashboard();
    }

    // Backend API helpers
    async function apiFetch(url, options = {}) {
      const finalOptions = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        ...options
      };
      const res = await fetch(url, finalOptions);
      if (res.status === 401) {
        showToast('Session expired. Please log in again.', 'warning');
        handleLogout();
        throw new Error('Unauthorized');
      }
      const contentType = res.headers.get('content-type') || '';
      const data = contentType.includes('application/json') ? await res.json() : null;
      if (!res.ok) {
        const message = (data && (data.error || data.message)) || `Request failed: ${res.status}`;
        throw new Error(message);
      }
      return data;
    }

    function mapBackendTaskToUI(t) {
      return {
        id: t.id,
        orderNo: t.order_no,
        customerName: t.customer_name,
        contactNumber: t.contact_number,
        serviceType: t.service_type,
        status: t.status,
        assignedTo: t.assigned_to,
        branch: t.branch_code,
        paymode: t.paymode,
        servicePrice: t.service_price,
        paidAmount: t.paid_amount,
        serviceCharge: t.service_charge,
        description: t.description,
        edited: t.edited,
        editReason: t.edit_reason,
        sharedWith: Array.isArray(t.shared_with) ? t.shared_with : [],
        date: t.task_date,
        timestamp: t.created_at,
        takenOverBy: null
      };
    }

    function mapUIToBackendTask(d) {
      return {
        customer_name: d.customerName,
        contact_number: d.contactNumber,
        service_type: d.serviceType,
        assigned_to: d.assignedTo,
        branch_code: d.branchCode || d.branch,
        paymode: d.paymode,
        service_price: d.servicePrice,
        paid_amount: d.paidAmount,
        service_charge: d.serviceCharge,
        description: d.description
      };
    }

    async function fetchTasksAndRender() {
      try {
        const data = await apiFetch('/api/tasks');
        tasks = data.map(mapBackendTaskToUI);
        renderTasks();
        updateDashboard();
      } catch (err) {
        console.error(err);
        showToast(`Failed to load tasks: ${err.message}`, 'error');
      }
    }

    async function loadServicesFromBackend() {
      try {
        const data = await apiFetch('/api/services');
        serviceDatabase = data;
        populateServiceDatabase();
        populateServiceDropdown();
      } catch (err) {
        console.error(err);
      }
    }

    // Handle login
    function handleLogin(e) {
      e.preventDefault();
      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      apiFetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      })
      .then(res => {
        if (!res || !res.user) throw new Error('Invalid server response');
        currentUser = { username: res.user.username, role: res.user.role, id: res.user.id, email: res.user.email };
        sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
        showApp();
        showToast('Login successful!', 'success');
      })
      .catch(err => {
        showToast(err.message || 'Invalid credentials. Please try again.', 'error');
      });
    }

    // Handle logout
    function handleLogout() {
      apiFetch('/api/logout', { method: 'POST' }).catch(() => {});
      currentUser = null;
      sessionStorage.removeItem('currentUser');
      showLogin();
      showToast('You have been logged out.', 'warning');
    }

    // Navigate to different pages
    function navigateToPage(page) {
      // Hide all pages
      dashboardPage.classList.add('hidden');
      tasksPage.classList.add('hidden');
      staffPage.classList.add('hidden');
      reportsPage.classList.add('hidden');
      databasePage.classList.add('hidden');
      staffPanelPage.classList.add('hidden');
      
      // Remove active class from all nav links
      navLinks.forEach(link => link.classList.remove('active'));
      
      // Show the selected page and set active nav link
      switch(page) {
        case 'dashboard':
          dashboardPage.classList.remove('hidden');
          document.querySelector('[data-page="dashboard"]').classList.add('active');
          updateDashboard();
          break;
        case 'tasks':
          tasksPage.classList.remove('hidden');
          document.querySelector('[data-page="tasks"]').classList.add('active');
          break;
        case 'staff':
          staffPage.classList.remove('hidden');
          document.querySelector('[data-page="staff"]').classList.add('active');
          updateStaffAlerts();
          break;
        case 'reports':
          reportsPage.classList.remove('hidden');
          document.querySelector('[data-page="reports"]').classList.add('active');
          updateReports();
          break;
        case 'database':
          databasePage.classList.remove('hidden');
          document.querySelector('[data-page="database"]').classList.add('active');
          break;
        case 'staff-panel':
          staffPanelPage.classList.remove('hidden');
          document.querySelector('[data-page="staff-panel"]').classList.add('active');
          updateStaffPanel();
          break;
      }
      
      currentPage = page;
    }

    // Update Staff Panel
    function updateStaffPanel() {
      if (!currentUser || currentUser.role !== 'staff') return;
      
      // Set current staff name
      currentStaffName.textContent = currentUser.username;
      
      // Calculate statistics
      const totalTasks = tasks.length;
      const pendingTasks = tasks.filter(task => task.status === 'Pending').length;
      const myTasks = tasks.filter(task => 
        task.assignedTo === currentUser.username || task.takenOverBy === currentUser.username
      ).length;
      const extraTasks = tasks.filter(task => task.takenOverBy === currentUser.username).length;
      
      // Update statistics cards
      staffTotalTasks.textContent = totalTasks;
      staffPendingTasks.textContent = pendingTasks;
      staffMyTasks.textContent = myTasks;
      staffExtraTasks.textContent = extraTasks;
      
      // Populate task containers
      populateAllTasks();
      populateMyTasks();
      populateExtraTasks();
    }

    // Populate All Tasks
    function populateAllTasks() {
      allTasksContainer.innerHTML = '';
      
      tasks.forEach(task => {
        const taskCard = createTaskCard(task, 'all');
        allTasksContainer.appendChild(taskCard);
      });
    }

    // Populate My Tasks
    function populateMyTasks() {
      myTasksContainer.innerHTML = '';
      
      const myTasks = tasks.filter(task => 
        task.assignedTo === currentUser.username || task.takenOverBy === currentUser.username
      );
      
      myTasks.forEach(task => {
        const taskCard = createTaskCard(task, 'my');
        myTasksContainer.appendChild(taskCard);
      });
    }

    // Populate Extra Tasks
    function populateExtraTasks() {
      extraTasksContainer.innerHTML = '';
      
      const extraTasks = tasks.filter(task => task.takenOverBy === currentUser.username);
      
      if (extraTasks.length === 0) {
        extraTasksContainer.innerHTML = '<p class="text-center">No extra tasks taken over yet.</p>';
        return;
      }
      
      extraTasks.forEach(task => {
        const taskCard = createTaskCard(task, 'extra');
        extraTasksContainer.appendChild(taskCard);
      });
    }

    // Create Task Card for Staff Panel
function createTaskCard(task, type) {
  const taskCard = document.createElement('div');
  taskCard.className = `task-card ${type === 'extra' ? 'extra-task' : ''}`;
  
  const isMyTask = task.assignedTo === currentUser.username || task.takenOverBy === currentUser.username;
  const isTakenOver = task.takenOverBy === currentUser.username;
  const canTakeOver = !isMyTask && task.takenOverBy === null;
  
  taskCard.innerHTML = `
    <div class="task-card-header">
      <div>
        <strong>${task.orderNo}</strong> - ${task.customerName}
        ${isTakenOver ? '<span class="badge bg-warning">Taken Over</span>' : ''}
      </div>
      <div>
        <span class="status status-${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span>
      </div>
    </div>
    <div class="task-card-body">
      <div class="task-info">
        <strong>Service:</strong> ${task.serviceType}
      </div>
      <div class="task-info">
        <strong>Branch:</strong> ${task.branch}
      </div>
      <div class="task-info">
        <strong>Assigned To:</strong> ${task.assignedTo}
      </div>
      <div class="task-info">
        <strong>Contact:</strong> ${task.contactNumber}
      </div>
      <div class="task-info">
        <strong>Date:</strong> ${new Date(task.timestamp).toLocaleDateString()}
      </div>
    </div>
    <div class="task-actions">
      ${canTakeOver ? `<button class="action-btn takeover-btn" data-task-id="${task.id}">Take Over</button>` : ''}
      ${isMyTask ? `
        <button class="action-btn edit-btn" data-task-id="${task.id}">Edit</button>
        <select class="status-select" data-task-id="${task.id}">
          <option value="Received" ${task.status === 'Received' ? 'selected' : ''}>Received</option>
          <option value="Pending" ${task.status === 'Pending' ? 'selected' : ''}>Pending</option>
          <option value="In Progress" ${task.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
          <option value="Completed" ${task.status === 'Completed' ? 'selected' : ''}>Completed</option>
          <option value="Hold" ${task.status === 'Hold' ? 'selected' : ''}>Hold</option>
          <option value="Cancelled" ${task.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
        </select>
      ` : ''}
    </div>
  `;
  
  // Add event listeners
  if (canTakeOver) {
    taskCard.querySelector('.takeover-btn').addEventListener('click', () => takeOverTask(task.id));
  }
  
  if (isMyTask) {
    taskCard.querySelector('.edit-btn').addEventListener('click', () => editTask(task.id));
    taskCard.querySelector('.status-select').addEventListener('change', (e) => {
      updateTaskStatus(task.id, e.target.value);
    });
  }
  
  return taskCard;
}
    // Take Over Task
    function takeOverTask(taskId) {
      const taskIndex = tasks.findIndex(t => t.id === taskId);
      if (taskIndex !== -1) {
        tasks[taskIndex].takenOverBy = currentUser.username;
        tasks[taskIndex].edited = true;
        tasks[taskIndex].editReason = `Task taken over by ${currentUser.username}`;
        
        updateStaffPanel();
        showToast('Task taken over successfully!', 'success');
      }
    }

    // Switch Tabs in Staff Panel
    function switchTab(tabId) {
      // Update tab buttons
      tabButtons.forEach(button => {
        button.classList.toggle('active', button.getAttribute('data-tab') === tabId);
      });
      
      // Update tab contents
      tabContents.forEach(content => {
        content.classList.toggle('active', content.id === tabId);
      });
    }

    // Filter All Tasks
    function filterAllTasks() {
      const searchTerm = allTasksSearch.value.toLowerCase();
      const taskCards = allTasksContainer.querySelectorAll('.task-card');
      
      taskCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? '' : 'none';
      });
    }

    // Update task status (for staff)
    function updateTaskStatus(id, newStatus) {
      const taskIndex = tasks.findIndex(t => t.id === id);
      if (taskIndex === -1) {
        showToast('Task not found', 'error');
        return;
      }

      const oldStatus = tasks[taskIndex].status;
      
      // Update status in database via API
      apiFetch(`/api/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ status: newStatus })
      })
      .then(() => {
        // Update local state only after successful API call
        tasks[taskIndex].status = newStatus;
        tasks[taskIndex].edited = true;
        tasks[taskIndex].editReason = `Status changed from ${oldStatus} to ${newStatus}`;
        
        // Show status update modal
        statusOrderNo.textContent = tasks[taskIndex].orderNo;
        statusNewStatus.textContent = newStatus;
        statusUpdateModal.style.display = 'flex';
        
        renderTasks();
        updateDashboard();
        updateStaffPanel();
        showToast('Task status updated successfully!', 'success');
      })
      .catch(err => {
        showToast(`Failed to update task status: ${err.message}`, 'error');
        // Revert the select dropdown to previous value (handle both data attributes)
        const selectElement = document.querySelector(`.status-select[data-task-id="${id}"], .status-select[data-id="${id}"]`);
        if (selectElement) {
          selectElement.value = oldStatus;
        }
      });
    }

    // Populate staff dropdown
    function populateStaffDropdown() {
      assignedToSelect.innerHTML = '<option value="">Assign Staff</option>';
      filterStaff.innerHTML = '<option value="all">All Staff</option>';
      
      // Load from backend if authorized; otherwise minimal fallback
      apiFetch('/api/users')
        .then(users => {
          STAFF_LIST = users.map(u => ({ name: u.username, role: u.role, email: u.email }));
          STAFF_LIST.filter(s => s.role === 'staff').forEach(staff => {
            const option = document.createElement('option');
            option.value = staff.name;
            option.textContent = staff.name;
            assignedToSelect.appendChild(option);
            const filterOption = document.createElement('option');
            filterOption.value = staff.name;
            filterOption.textContent = staff.name;
            filterStaff.appendChild(filterOption);
          });
        })
        .catch(() => {
          // If not permitted (staff role), fallback to current user only
          if (currentUser && currentUser.role === 'staff') {
            const option = document.createElement('option');
            option.value = currentUser.username;
            option.textContent = currentUser.username;
            assignedToSelect.appendChild(option);
            const filterOption = document.createElement('option');
            filterOption.value = currentUser.username;
            filterOption.textContent = currentUser.username;
            filterStaff.appendChild(filterOption);
          }
        });
    }

    // Populate service dropdown
    function populateServiceDropdown() {
      serviceTypeSelect.innerHTML = '<option value="">Select Service</option>';
      filterService.innerHTML = '<option value="all">All Services</option>';
      
      serviceDatabase.forEach(service => {
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

    // Populate filter dropdowns
    function populateFilterDropdowns() {
      // Already populated staff and service dropdowns above
    }

    // Populate staff list
    function populateStaffList() {
      staffListContainer.innerHTML = '';
      apiFetch('/api/users')
        .then(users => {
          users.forEach(user => {
            const card = document.createElement('div');
            card.className = 'staff-card';
            card.innerHTML = `
              <div class="staff-avatar">${user.username.charAt(0)}</div>
              <div class="staff-name">${user.username}</div>
              <div class="staff-role">${user.role.charAt(0).toUpperCase() + user.role.slice(1)}</div>
              <div class="staff-email">${user.email || ''}</div>
            `;
            staffListContainer.appendChild(card);
          });
        })
        .catch(() => {
          // Fallback to existing in-memory list if not authorized
          STAFF_LIST.forEach(staff => {
            const card = document.createElement('div');
            card.className = 'staff-card';
            card.innerHTML = `
              <div class="staff-avatar">${staff.name.charAt(0)}</div>
              <div class="staff-name">${staff.name}</div>
              <div class="staff-role">${staff.role.charAt(0).toUpperCase() + staff.role.slice(1)}</div>
              <div class="staff-email">${staff.email}</div>
            `;
            staffListContainer.appendChild(card);
          });
        });
    }

    // Populate service database
    function populateServiceDatabase() {
      serviceListContainer.innerHTML = '';
      
      serviceDatabase.forEach(service => {
        const serviceItem = document.createElement('div');
        serviceItem.className = 'service-item';
        serviceItem.innerHTML = `
          <div><strong>${service.name}</strong></div>
          <div>Price: ₹${service.price} | Fee: ₹${service.fee} | Charge: ₹${service.charge}</div>
          <div>Link: <a href="${service.link}" target="_blank">${service.link}</a></div>
          <div>Note: ${service.note}</div>
          ${currentUser.role !== 'staff' ? `<div class="mt-1">
            <button class="action-btn edit-btn" data-service-id="${service.id}">Edit</button>
            <button class="action-btn delete-btn" data-service-id="${service.id}">Delete</button>
          </div>` : ''}
        `;
        
        // Check for duplicates
        const duplicates = serviceDatabase.filter(s => 
          s.name.toLowerCase() === service.name.toLowerCase() && s.id !== service.id
        );
        
        if (duplicates.length > 0) {
          serviceItem.classList.add('duplicate');
          const duplicateAlert = document.createElement('div');
          duplicateAlert.className = 'text-danger';
          duplicateAlert.textContent = '⚠️ Duplicate service name detected';
          serviceItem.appendChild(duplicateAlert);
        }
        
        serviceListContainer.appendChild(serviceItem);
        
        // Add event listeners for edit and delete buttons
        if (currentUser.role !== 'staff') {
          serviceItem.querySelector('.edit-btn').addEventListener('click', () => editService(service.id));
          serviceItem.querySelector('.delete-btn').addEventListener('click', () => deleteService(service.id));
        }
      });
    }

    // Show task form
    function showTaskForm() {
      taskFormContainer.classList.remove('hidden');
      formTitle.textContent = 'Create New Task';
      taskForm.reset();
      editingTaskId = null;
    }

    // Hide task form
    function hideTaskForm() {
      taskFormContainer.classList.add('hidden');
    }

    // Show service form
    function showServiceForm() {
      serviceFormContainer.classList.remove('hidden');
      serviceFormTitle.textContent = 'Add New Service';
      serviceForm.reset();
      editingServiceId = null;
    }

    // Hide service form
    function hideServiceForm() {
      serviceFormContainer.classList.add('hidden');
    }

    // Handle task form submission
   function handleTaskSubmit(e) {
  e.preventDefault();
  
  // If editing an existing task and user is staff, show reason modal
  if (editingTaskId !== null && currentUser.role === 'staff') {
    editReasonModal.style.display = 'flex';
    return;
  }
      
      // Otherwise, save the task directly
      saveTask();
    }

    // Handle service form submission
    function handleServiceSubmit(e) {
      e.preventDefault();
      saveService();
    }

    // Save task with reason (for staff)
    function saveTaskWithReason() {
      currentEditReason = editReason.value.trim();
      if (!currentEditReason) {
        showToast('Please provide a reason for the change.', 'error');
        return;
      }
      
      editReasonModal.style.display = 'none';
      saveTask();
    }

    // Save task to the backend
    function saveTask() {
      const taskData = {
        branchCode: document.getElementById('branchCode').value,
        customerName: document.getElementById('customerName').value,
        contactNumber: document.getElementById('contactNumber').value,
        serviceType: document.getElementById('serviceType').value,
        assignedTo: document.getElementById('assignedTo').value,
        paymode: document.getElementById('paymode').value,
        servicePrice: parseFloat(document.getElementById('servicePrice').value) || 0,
        paidAmount: parseFloat(document.getElementById('paidAmount').value) || 0,
        serviceCharge: parseFloat(document.getElementById('serviceCharge').value) || 0,
        description: document.getElementById('description').value
      };

      const payload = mapUIToBackendTask(taskData);

      const request = editingTaskId === null
        ? apiFetch('/api/tasks', { method: 'POST', body: JSON.stringify(payload) })
        : apiFetch(`/api/tasks/${editingTaskId}`, { method: 'PUT', body: JSON.stringify({ ...payload, edit_reason: currentEditReason }) });

      request
        .then(() => {
          showToast(editingTaskId === null ? 'Task created successfully!' : 'Task updated successfully!', 'success');
          hideTaskForm();
          editReason.value = '';
          currentEditReason = '';
          editingTaskId = null;
          return fetchTasksAndRender();
        })
        .catch(err => {
          showToast(`Failed to save task: ${err.message}`, 'error');
        });
    }

    // Save service to database via backend API
    function saveService() {
      const serviceData = {
        name: document.getElementById('serviceName').value,
        price: parseFloat(document.getElementById('servicePriceDB').value) || 0,
        fee: parseFloat(document.getElementById('serviceFee').value) || 0,
        charge: parseFloat(document.getElementById('serviceChargeDB').value) || 0,
        link: document.getElementById('serviceLink').value,
        note: document.getElementById('serviceNote').value
      };

      const request = editingServiceId === null
        ? apiFetch('/api/services', { method: 'POST', body: JSON.stringify(serviceData) })
        : apiFetch(`/api/services/${editingServiceId}`, { method: 'PUT', body: JSON.stringify(serviceData) });

      request
        .then(() => {
          showToast(editingServiceId === null ? 'Service added successfully!' : 'Service updated successfully!', 'success');
          hideServiceForm();
          editingServiceId = null;
          return loadServicesFromBackend();
        })
        .catch(err => {
          showToast(`Failed to save service: ${err.message}`, 'error');
        });
    }

    // Edit a service
    function editService(id) {
      const service = serviceDatabase.find(s => s.id === id);
      if (!service) return;
      
      document.getElementById('serviceName').value = service.name;
      document.getElementById('servicePriceDB').value = service.price;
      document.getElementById('serviceFee').value = service.fee;
      document.getElementById('serviceChargeDB').value = service.charge;
      document.getElementById('serviceLink').value = service.link;
      document.getElementById('serviceNote').value = service.note;
      
      serviceFormTitle.textContent = 'Edit Service';
      editingServiceId = id;
      serviceFormContainer.classList.remove('hidden');
    }

    // Delete a service via backend API
    function deleteService(id) {
      if (!confirm('Are you sure you want to delete this service?')) return;
      apiFetch(`/api/services/${id}`, { method: 'DELETE' })
        .then(() => {
          showToast('Service deleted successfully!', 'success');
          return loadServicesFromBackend();
        })
        .catch(err => {
          showToast(`Failed to delete service: ${err.message}`, 'error');
        });
    }

    // Render tasks in the table
    function renderTasks() {
      taskTableBody.innerHTML = '';
      recentTasksTable.innerHTML = '';
      overdueTasksTable.innerHTML = '';
      
      // Apply filters if any
      let filteredTasks = [...tasks];
      
      if (currentFilters.date !== 'all') {
        filteredTasks = filterTasksByDate(filteredTasks, currentFilters.date);
      }
      
      if (currentFilters.branch !== 'all') {
        filteredTasks = filteredTasks.filter(task => task.branch === currentFilters.branch);
      }
      
      if (currentFilters.staff !== 'all') {
        filteredTasks = filteredTasks.filter(task => task.assignedTo === currentFilters.staff);
      }
      
      if (currentFilters.status !== 'all') {
        filteredTasks = filteredTasks.filter(task => task.status === currentFilters.status);
      }
      
      if (currentFilters.service !== 'all') {
        filteredTasks = filteredTasks.filter(task => task.serviceType === currentFilters.service);
      }
      
      // Sort tasks by date (newest first)
      const sortedTasks = [...filteredTasks].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      
      // Display recent tasks (last 10) in dashboard
      const recentTasks = sortedTasks.slice(0, 10);
      recentTasks.forEach(task => {
        const row = createTaskRow(task, false);
        recentTasksTable.appendChild(row);
      });
      
      // Display overdue tasks
      const overdueTasks = sortedTasks.filter(task => {
        const taskTime = new Date(task.timestamp);
        const now = new Date();
        const hoursDiff = (now - taskTime) / (1000 * 60 * 60);
        
        return (task.status === 'Pending' || task.status === 'In Progress' || task.status === 'Hold') && 
               hoursDiff > 24;
      });
      
      if (overdueTasks.length > 0) {
        overdueTasksContainer.classList.remove('hidden');
        overdueTasks.forEach(task => {
          const taskTime = new Date(task.timestamp);
          const now = new Date();
          const hoursDiff = Math.floor((now - taskTime) / (1000 * 60 * 60));
          
          const row = document.createElement('tr');
          row.innerHTML = `
            <td>${task.orderNo}</td>
            <td>${task.customerName}</td>
            <td>${task.serviceType}</td>
            <td><span class="status status-${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span></td>
            <td>${task.assignedTo}</td>
            <td>${new Date(task.timestamp).toLocaleDateString()}</td>
            <td>${hoursDiff} hours</td>
          `;
          overdueTasksTable.appendChild(row);
        });
      } else {
        overdueTasksContainer.classList.add('hidden');
      }
      
      // Display all tasks in tasks page
      sortedTasks.forEach(task => {
        const row = createTaskRow(task, true);
        taskTableBody.appendChild(row);
      });
    }

    // Filter tasks by date
    function filterTasksByDate(tasks, dateFilter) {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      
      switch(dateFilter) {
        case 'today':
          return tasks.filter(task => {
            const taskDate = new Date(task.timestamp);
            return taskDate >= today && taskDate < tomorrow;
          });
        case 'yesterday':
          return tasks.filter(task => {
            const taskDate = new Date(task.timestamp);
            return taskDate >= yesterday && taskDate < today;
          });
        case 'tomorrow':
          return tasks.filter(task => {
            const taskDate = new Date(task.timestamp);
            return taskDate >= tomorrow && taskDate < new Date(tomorrow.getTime() + 24 * 60 * 60 * 1000);
          });
        case 'custom':
          if (customDate.value) {
            const custom = new Date(customDate.value);
            const nextDay = new Date(custom);
            nextDay.setDate(nextDay.getDate() + 1);
            
            return tasks.filter(task => {
              const taskDate = new Date(task.timestamp);
              return taskDate >= custom && taskDate < nextDay;
            });
          }
          return tasks;
        default:
          return tasks;
      }
    }

    // Create a task row for the table
 // Create a task row for the table
function createTaskRow(task, includeActions) {
  const row = document.createElement('tr');
  
  // Format date for display
  const taskDate = new Date(task.timestamp);
  const formattedDate = taskDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
  
  row.innerHTML = `
    <td>${task.orderNo}${task.edited ? '<span class="edit-indicator" title="Edited">✏️</span>' : ''}</td>
    <td>${task.customerName}</td>
    <td>${task.serviceType}</td>
    <td>
      <span class="status status-${task.status.toLowerCase().replace(' ', '-')}">${task.status}</span>
    </td>
    <td>${task.assignedTo}</td>
    <td>${task.sharedWith && task.sharedWith.length > 0 ? task.sharedWith.join(', ') : '<span class="text-muted">—</span>'}</td>
    <td>${formattedDate}</td>
    <td>${task.contactNumber}</td>
  `;
  
  if (includeActions) {
    const actionsCell = document.createElement('td');
    
    // Different actions based on user role
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
      // Staff can edit tasks assigned to them or shared with them
      const canEdit = task.assignedTo === currentUser.username || task.sharedWith.includes(currentUser.username);
      
      if (canEdit) {
        actionsCell.innerHTML = `
          <button class="action-btn edit-btn" data-id="${task.id}">Edit</button>
          <button class="action-btn share-task-btn" data-id="${task.id}">Share</button>
          <select class="status-select" data-id="${task.id}">
            <option value="Received" ${task.status === 'Received' ? 'selected' : ''}>Received</option>
            <option value="Pending" ${task.status === 'Pending' ? 'selected' : ''}>Pending</option>
            <option value="In Progress" ${task.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
            <option value="Completed" ${task.status === 'Completed' ? 'selected' : ''}>Completed</option>
            <option value="Hold" ${task.status === 'Hold' ? 'selected' : ''}>Hold</option>
            <option value="Cancelled" ${task.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
          </select>
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
    }
    
    row.appendChild(actionsCell);
    
    // Add event listeners to action buttons
    if (currentUser.role === 'admin' || currentUser.role === 'manager') {
      actionsCell.querySelector('.edit-btn').addEventListener('click', () => editTask(task.id));
    }
    
    if (currentUser.role === 'admin') {
      actionsCell.querySelector('.delete-btn').addEventListener('click', () => deleteTask(task.id));
    }
    
    // Add event listeners for staff edit button
    if (currentUser.role === 'staff') {
      const editBtn = actionsCell.querySelector('.edit-btn');
      if (editBtn) {
        editBtn.addEventListener('click', () => editTask(task.id));
      }
    }
    
    // Add event listener to status select for all roles
    const statusSelect = actionsCell.querySelector('.status-select');
    if (statusSelect) {
      statusSelect.addEventListener('change', (e) => {
        updateTaskStatus(task.id, e.target.value);
      });
    }
    
    // Add event listener to share button for all roles
    actionsCell.querySelector('.share-task-btn').addEventListener('click', () => showShareModal(task.id));
  }
  
  return row;
}

    // Edit a task
   // Edit a task
function editTask(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  
  // Check if staff is allowed to edit this task
  if (currentUser.role === 'staff') {
    if (task.assignedTo !== currentUser.username && !task.sharedWith.includes(currentUser.username)) {
      showToast('You can only edit tasks assigned to you or shared with you', 'error');
      return;
    }
  }
  
  document.getElementById('branchCode').value = task.branch;
  document.getElementById('customerName').value = task.customerName;
  document.getElementById('contactNumber').value = task.contactNumber;
  document.getElementById('serviceType').value = task.serviceType;
  document.getElementById('assignedTo').value = task.assignedTo;
  document.getElementById('paymode').value = task.paymode;
  document.getElementById('servicePrice').value = task.servicePrice;
  document.getElementById('paidAmount').value = task.paidAmount;
  document.getElementById('serviceCharge').value = task.serviceCharge;
  document.getElementById('description').value = task.description;
  
  formTitle.textContent = 'Edit Task';
  editingTaskId = id;
  taskFormContainer.classList.remove('hidden');
  taskFormContainer.scrollIntoView({ behavior: 'smooth' });

    }

    // Delete a task
    function deleteTask(id) {
      if (!confirm('Are you sure you want to delete this task?')) return;
      
      apiFetch(`/api/tasks/${id}`, { method: 'DELETE' })
        .then(() => {
          tasks = tasks.filter(t => t.id !== id);
          renderTasks();
          updateDashboard();
          showToast('Task deleted successfully!', 'success');
        })
        .catch(err => {
          showToast(`Failed to delete task: ${err.message}`, 'error');
        });
    }

    // Show share task modal
    function showShareModal(id) {
      sharingTaskId = id;
      staffListModal.innerHTML = '';
      
      const task = tasks.find(t => t.id === id);
      STAFF_LIST.forEach(staff => {
        if (staff.name !== task.assignedTo && staff.role === 'staff') {
          const staffItem = document.createElement('div');
          staffItem.className = 'staff-item';
          staffItem.textContent = staff.name;
          staffItem.dataset.staff = staff.name;
          staffListModal.appendChild(staffItem);
        }
      });
      
      const staffItems = staffListModal.querySelectorAll('.staff-item');
      staffItems.forEach(item => {
        item.addEventListener('click', () => {
          staffItems.forEach(i => i.classList.remove('selected'));
          item.classList.add('selected');
        });
      });
      
      shareTaskModal.style.display = 'flex';
    }

    // Share task with selected staff
    function shareTask() {
      const selectedStaffItem = staffListModal.querySelector('.selected');
      if (!selectedStaffItem) {
        showToast('Please select a staff member to share with.', 'error');
        return;
      }
      
      const staffName = selectedStaffItem.dataset.staff;
      
      apiFetch(`/api/tasks/${sharingTaskId}/share`, {
        method: 'POST',
        body: JSON.stringify({ staff_name: staffName })
      })
        .then(() => {
          shareTaskModal.style.display = 'none';
          showToast(`Task shared with ${staffName} successfully!`, 'success');
          // Refresh tasks from backend to get updated shared_with data
          return fetchTasksAndRender();
        })
        .then(() => {
          // Also update staff panel if we're on that page
          if (currentPage === 'staff-panel') {
            updateStaffPanel();
          }
        })
        .catch(err => {
          showToast(`Failed to share task: ${err.message}`, 'error');
        });
    }

    // Filter tasks based on search input
    function filterTasks() {
      const searchTerm = taskSearch.value.toLowerCase();
      const rows = taskTableBody.querySelectorAll('tr');
      
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
      });
    }

    // Filter services based on search input
    function filterServices() {
      const searchTerm = serviceSearch.value.toLowerCase();
      const items = serviceListContainer.querySelectorAll('.service-item');
      
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? '' : 'none';
      });
    }

    // Apply task filters
    function applyTaskFilters() {
      currentFilters = {
        date: filterDate.value,
        branch: filterBranch.value,
        staff: filterStaff.value,
        status: filterStatus.value,
        service: filterService.value
      };
      
      renderTasks();
      showToast('Filters applied successfully!', 'success');
    }

    // Reset task filters
    function resetTaskFilters() {
      filterDate.value = 'all';
      filterBranch.value = 'all';
      filterStaff.value = 'all';
      filterStatus.value = 'all';
      filterService.value = 'all';
      customDateContainer.style.display = 'none';
      
      currentFilters = {
        date: 'all',
        branch: 'all',
        staff: 'all',
        status: 'all',
        service: 'all'
      };
      
      renderTasks();
      showToast('Filters reset successfully!', 'success');
    }

    // Show service tooltip
    function showServiceTooltip(e) {
      const selectedOption = e.target.options[e.target.selectedIndex];
      if (selectedOption && selectedOption.dataset.serviceId) {
        const serviceId = parseInt(selectedOption.dataset.serviceId);
        const service = serviceDatabase.find(s => s.id === serviceId);
        
        if (service) {
          serviceTooltip.innerHTML = `
            <strong>${service.name}</strong><br>
            Price: ₹${service.price}<br>
            Fee: ₹${service.fee}<br>
            Charge: ₹${service.charge}<br>
            Note: ${service.note}
          `;
          serviceTooltip.classList.add('show');
          
          const rect = e.target.getBoundingClientRect();
          serviceTooltip.style.top = `${rect.bottom + window.scrollY}px`;
          serviceTooltip.style.left = `${rect.left + window.scrollX}px`;
        }
      }
    }

    // Hide service tooltip
    function hideServiceTooltip() {
      serviceTooltip.classList.remove('show');
    }

    // Update service details in form when service is selected
    function updateServiceDetails(e) {
      const selectedOption = e.target.options[e.target.selectedIndex];
      if (selectedOption && selectedOption.dataset.serviceId) {
        const serviceId = parseInt(selectedOption.dataset.serviceId);
        const service = serviceDatabase.find(s => s.id === serviceId);
        
        if (service) {
          document.getElementById('servicePrice').value = service.price;
          document.getElementById('serviceCharge').value = service.charge;
        }
      }
    }

    // Update dashboard statistics from backend
    function updateDashboard() {
      apiFetch('/api/dashboard/stats')
        .then(stats => {
          document.getElementById('totalTasks').textContent = stats.total_tasks;
          document.getElementById('tasksToday').textContent = stats.tasks_today;
          document.getElementById('completedTasks').textContent = stats.completed_tasks;
          if (currentUser.role === 'admin') {
            document.getElementById('totalRevenue').textContent = `₹${(stats.total_revenue || 0).toLocaleString()}`;
          }
          return updateWinners();
        })
        .then(() => updateOverdueTasks())
        .catch(() => {});
    }

    // Update winners from backend
    function updateWinners() {
      winnersCards.innerHTML = '';
      return apiFetch('/api/dashboard/top-performers')
        .then(top => {
          if (Array.isArray(top) && top.length > 0) {
            winnersContainer.classList.remove('hidden');
            top.forEach((winner, index) => {
              const card = document.createElement('div');
              card.className = `winner-card ${index === 0 ? '' : index === 1 ? 'second' : 'third'}`;
              const place = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
              card.innerHTML = `
                <h4>${place} ${winner.name}</h4>
                <p>Completed Tasks: <strong>${winner.completed_tasks}</strong></p>
                ${currentUser.role === 'admin' ? `<p>Revenue: <strong>₹${(winner.total_revenue || 0).toLocaleString()}</strong></p>` : ''}
                <p>Score: <strong>${Math.round(winner.score)}</strong></p>
              `;
              winnersCards.appendChild(card);
            });
          } else {
            winnersContainer.classList.add('hidden');
          }
        })
        .catch(() => {
          winnersContainer.classList.add('hidden');
        });
    }

    // Update overdue tasks from backend
    function updateOverdueTasks() {
      overdueTasksTable.innerHTML = '';
      return apiFetch('/api/dashboard/overdue-tasks')
        .then(list => {
          if (Array.isArray(list) && list.length > 0) {
            overdueTasksContainer.classList.remove('hidden');
            list.forEach(task => {
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
        })
        .catch(() => {
          overdueTasksContainer.classList.add('hidden');
        });
    }

    // Update staff alerts
    function updateStaffAlerts() {
      staffAlertsContainer.innerHTML = '';
      
      const staffUsernames = Array.from(new Set(tasks.map(t => t.assignedTo).filter(Boolean)));
      staffUsernames.forEach(name => {
        const staffTasks = tasks.filter(task => task.assignedTo === name);
        const overdueTasks = staffTasks.filter(task => {
          const taskTime = new Date(task.timestamp);
          const now = new Date();
          const hoursDiff = (now - taskTime) / (1000 * 60 * 60);
          
          return (task.status === 'Pending' || task.status === 'In Progress' || task.status === 'Hold') && 
                 hoursDiff > 24;
        });
        
        if (overdueTasks.length > 0) {
          const alertCard = document.createElement('div');
          alertCard.className = 'report-card alert-badge';
          alertCard.innerHTML = `
            <h4>${name}</h4>
            <p>Overdue Tasks: <strong>${overdueTasks.length}</strong></p>
            <div class="staff-alert">
              <h5>Overdue Tasks for ${name}:</h5>
              <ul>
                ${overdueTasks.map(task => `
                  <li>
                    <strong>${task.orderNo}</strong><br>
                    Mobile: ${task.contactNumber}<br>
                    Query: ${task.serviceType}
                  </li>
                `).join('')}
              </ul>
            </div>
          `;
          
          staffAlertsContainer.appendChild(alertCard);
          
          alertCard.addEventListener('mouseenter', (e) => {
            const alert = alertCard.querySelector('.staff-alert');
            alert.classList.add('show');
            
            const rect = alertCard.getBoundingClientRect();
            alert.style.top = `${rect.bottom + window.scrollY}px`;
            alert.style.left = `${rect.left + window.scrollX}px`;
          });
          
          alertCard.addEventListener('mouseleave', () => {
            const alert = alertCard.querySelector('.staff-alert');
            alert.classList.remove('show');
          });
        }
      });
    }

    // Update reports
    function updateReports() {
      staffPerformanceCards.innerHTML = '';
      
      const staffUsernames = Array.from(new Set(tasks.map(t => t.assignedTo).filter(Boolean)));
      staffUsernames.forEach(name => {
        const staffTasks = tasks.filter(task => task.assignedTo === name);
        const completedTasks = staffTasks.filter(task => task.status === 'Completed').length;
        const totalRevenue = staffTasks.reduce((sum, task) => sum + task.paidAmount, 0);
        const card = document.createElement('div');
        card.className = 'report-card';
        card.innerHTML = `
          <h4>${name}</h4>
          <p>Total Tasks: <strong>${staffTasks.length}</strong></p>
          <p>Completed: <strong>${completedTasks}</strong></p>
          ${currentUser.role === 'admin' ? `<p>Revenue: <strong>₹${totalRevenue.toLocaleString()}</strong></p>` : ''}
        `;
        staffPerformanceCards.appendChild(card);
      });
    }

    // Show add staff form (for admin only)
    function showAddStaffForm() {
      const username = prompt('Enter staff username:');
      if (!username) return;
      const email = prompt('Enter staff email:');
      if (!email) return;
      const password = prompt('Set a password for this user:');
      if (!password) return;

      apiFetch('/api/users', { method: 'POST', body: JSON.stringify({ username, email, password, role: 'staff' }) })
        .then(() => {
          showToast('Staff user created successfully!', 'success');
          populateStaffDropdown();
          populateStaffList();
        })
        .catch(err => {
          showToast(`Failed to create user: ${err.message}`, 'error');
        });
    }

    // Show toast notification
    function showToast(message, type = 'success') {
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

