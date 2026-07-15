<template>
  <div>
    <nav class="navbar navbar-expand navbar-dark bg-dark px-3 mb-4 rounded shadow-sm">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1 small">PPA Central Admin Engine</span>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'dashboard' }" href="#" @click.prevent="currentTab = 'dashboard'">Dashboard</a></li>
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'students' }" href="#" @click.prevent="currentTab = 'students'">Students</a></li>
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'companies' }" href="#" @click.prevent="currentTab = 'companies'">Companies</a></li>
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'drives' }" href="#" @click.prevent="currentTab = 'drives'">Drives</a></li>
          </ul>
          <button class="btn btn-outline-light btn-sm" @click="logout">Sign Out</button>
        </div>
      </div>
    </nav>
  
    <div class="container-fluid">
      <!-- Dashboard Tab -->
      <div v-if="currentTab === 'dashboard'" class="row g-3 mb-4">
        <div class="col-md-4"><div class="card bg-primary text-white p-3 border-0"><h6>Students</h6><h3>{{ stats.total_students }}</h3></div></div>
        <div class="col-md-4"><div class="card bg-success text-white p-3 border-0"><h6>Companies</h6><h3>{{ stats.total_companies }}</h3></div></div>
        <div class="col-md-4"><div class="card bg-warning text-dark p-3 border-0"><h6>Active Drives</h6><h3>{{ stats.total_drives }}</h3></div></div>
      </div>
  
      <!-- Students Tab -->
      <div v-if="currentTab === 'students'" class="card p-3 shadow-sm mb-4">
        <h5 class="fw-bold mb-2">Student Registrations</h5>
        <table class="table table-sm align-middle small">
          <thead><tr><th>Name</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="user in students" :key="user.id">
              <td>{{ user.name || user.username }}</td><td>{{ user.role }}</td>
              <td><span :class="['badge', user.status === 'Approved'?'bg-success':'bg-danger']">{{ user.status }}</span></td>
              <td>
                <button v-if="user.status !== 'Approved'" class="btn btn-xs btn-success py-0 px-1 me-1" @click="updateUser(user.id, 'Approved')">Approve</button>
                <button v-if="user.status !== 'Blacklisted'" class="btn btn-xs btn-danger py-0 px-1" @click="updateUser(user.id, 'Blacklisted')">Blacklist</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Companies Tab -->
      <div v-if="currentTab === 'companies'" class="card p-3 shadow-sm mb-4">
        <h5 class="fw-bold mb-2">Company Registrations</h5>
        <table class="table table-sm align-middle small">
          <thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="user in companies" :key="user.id">
              <td>{{ user.name || user.username }}</td><td>{{ user.role }}</td>
              <td><span :class="['badge', user.status === 'Approved'?'bg-success':'bg-danger']">{{ user.status }}</span></td>
              <td>
                <button v-if="user.status !== 'Approved'" class="btn btn-xs btn-success py-0 px-1 me-1" @click="updateUser(user.id, 'Approved')">Approve</button>
                <button v-if="user.status !== 'Blacklisted'" class="btn btn-xs btn-danger py-0 px-1" @click="updateUser(user.id, 'Blacklisted')">Blacklist</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
  
      <!-- Drives Tab -->
      <div v-if="currentTab === 'drives'" class="card p-3 shadow-sm">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="fw-bold mb-0">Drive Management Approvals</h5>
          <button class="btn btn-sm btn-primary" @click="sendReminders" :disabled="isSendingReminders">
            <span v-if="isSendingReminders" class="spinner-border spinner-border-sm me-1"></span>
            Email Students About Open Drives
          </button>
        </div>
        <table class="table table-sm align-middle small">
          <thead><tr><th>Company</th><th>Job Title</th><th>Status</th><th>Actions</th></tr></thead>
          <tbody>
            <tr v-for="drive in drives" :key="drive.id">
              <td>{{ drive.company_name }}</td><td>{{ drive.job_title }}</td>
              <td><span :class="['badge', drive.status==='Approved'?'bg-success':'bg-warning text-dark']">{{ drive.status }}</span></td>
              <td>
                <button v-if="drive.status === 'Pending'" class="btn btn-xs btn-success py-0 px-1 me-1" @click="updateDrive(drive.id, 'Approved')">Approve</button>
                <button v-if="drive.status !== 'Closed'" class="btn btn-xs btn-secondary py-0 px-1" @click="updateDrive(drive.id, 'Closed')">Close</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() { return { currentTab: 'dashboard', stats: {}, users: [], drives: [], isSendingReminders: false }; },
  computed: {
    students() { return this.users.filter(u => u.role === 'student'); },
    companies() { return this.users.filter(u => u.role === 'company'); }
  },
    mounted() { this.loadData(); },
    methods: {
      async loadData() {
        const sRes = await fetch('/api/admin/stats'); this.stats = await sRes.json();
        const uRes = await fetch('/api/admin/users'); this.users = await uRes.json();
        const dRes = await fetch('/api/admin/drives'); this.drives = await dRes.json();
      },
      async updateUser(id, status) {
        await fetch(`/api/admin/users/${id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) });
        this.loadData();
      },
      async updateDrive(id, status) {
        await fetch(`/api/admin/drives/${id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) });
        this.loadData();
      },
      async sendReminders() {
        this.isSendingReminders = true;
        try {
          const res = await fetch('/api/admin/reminders/send', { method: 'POST' });
          const data = await res.json();
          alert(data.message);
        } catch (e) {
          alert('Failed to send reminders.');
        }
        this.isSendingReminders = false;
      },
      logout() { this.$emit('logout'); }
    }
  }
  </script>