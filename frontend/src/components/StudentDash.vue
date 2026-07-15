<template>
  <div>
    <nav class="navbar navbar-expand navbar-dark bg-primary px-3 mb-4 rounded shadow-sm">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1 small">Student Placement Console</span>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'profile' }" href="#" @click.prevent="currentTab = 'profile'">Profile</a></li>
            <li class="nav-item"><a class="nav-link" :class="{ active: currentTab === 'drives' }" href="#" @click.prevent="currentTab = 'drives'">Drives</a></li>
          </ul>
          <button class="btn btn-outline-light btn-sm" @click="logout">Sign Out</button>
        </div>
      </div>
    </nav>
  
    <div class="container-fluid">
      <!-- Profile Tab -->
      <div v-if="currentTab === 'profile'" class="row g-4 justify-content-center">
        <div class="col-md-8">
          <div class="card p-3 shadow-sm mb-4">
            <h5 class="fw-bold mb-2">My Profile</h5>
            <div class="mb-3 small">
              <strong>Name:</strong> {{ user.username }}<br>
              <strong>CGPA:</strong> {{ currentProfile.cgpa }}<br>
              <strong>Branch:</strong> {{ currentProfile.branch }}<br>
              <strong>Resume:</strong> 
              <a v-if="currentProfile.resume" :href="currentProfile.resume" target="_blank">View Resume</a>
              <span v-else class="text-muted">Not Uploaded</span>
            </div>
            
            <h6 class="fw-bold mb-2">Update Profile</h6>
            <form @submit.prevent="updateProfile">
              <div class="mb-2">
                <input type="number" step="0.01" class="form-control form-control-sm" placeholder="CGPA" v-model="profileForm.cgpa">
              </div>
              <div class="mb-2">
                <input type="text" class="form-control form-control-sm" placeholder="Branch" v-model="profileForm.branch">
              </div>
              <div class="mb-2">
                <input type="file" class="form-control form-control-sm" @change="handleFileUpload" accept=".pdf">
              </div>
              <button type="submit" class="btn btn-sm btn-primary w-100">Update Profile</button>
            </form>
          </div>
        </div>
      </div>
  
      <!-- Drives Tab -->
      <div v-if="currentTab === 'drives'" class="row g-4">
        <div class="col-md-7">
          <div class="card p-3 shadow-sm">
            <h5 class="fw-bold mb-3">Recruitment Openings</h5>
            <div class="card border mb-2 p-2" v-for="drive in drives" :key="drive.id">
              <div class="d-flex justify-content-between">
                <h6><strong>{{ drive.job_title }}</strong></h6>
                <span class="badge bg-secondary">{{ drive.company_name }}</span>
              </div>
              <p class="small text-muted mb-1">{{ drive.job_description }}</p>
              <div class="d-flex justify-content-between align-items-center mt-1">
                <span class="small text-info text-xs">Min CGPA: {{ drive.min_cgpa }} | Branch: {{ drive.branch_criteria }}</span>
                <button v-if="!drive.applied && drive.eligible" class="btn btn-sm btn-primary py-0 px-2" @click="applyToDrive(drive.id)">Apply</button>
                <button v-else-if="drive.applied" class="btn btn-sm btn-success py-0 px-2" disabled>Applied</button>
                <span v-else class="badge bg-danger">Ineligible</span>
              </div>
            </div>
          </div>
        </div>
  
        <div class="col-md-5">
          <div class="card p-3 shadow-sm">
            <div class="d-flex justify-content-between align-items-center mb-2">
              <h5 class="fw-bold mb-0">My Applications</h5>
              <button class="btn btn-sm btn-outline-secondary py-0 px-2" @click="triggerExport">CSV Export</button>
            </div>
            <table class="table table-sm small">
              <thead><tr><th>Company</th><th>Job</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="item in history" :key="item.id">
                  <td>{{ item.company_name }}</td><td>{{ item.job_title }}</td>
                  <td><span :class="['badge', item.status==='Selected'?'bg-success':item.status==='Rejected'?'bg-danger':'bg-warning text-dark']">{{ item.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['user'],
  data() { return { currentTab: 'profile', drives: [], history: [], currentProfile: {}, profileForm: { cgpa: '', branch: '' }, resumeFile: null }; },
  mounted() { this.loadDashboard(); },
  methods: {
    async loadDashboard() {
      const dRes = await fetch(`/api/student/drives?student_id=${this.user.user_id}`); this.drives = await dRes.json();
      const hRes = await fetch(`/api/student/history?student_id=${this.user.user_id}`); this.history = await hRes.json();
      
      const pRes = await fetch(`/api/student/profile?student_id=${this.user.user_id}`); 
      if (pRes.ok) {
        this.currentProfile = await pRes.json();
        this.profileForm.cgpa = this.currentProfile.cgpa;
        this.profileForm.branch = this.currentProfile.branch;
      }
    },
    async applyToDrive(driveId) {
      const res = await fetch('/api/student/apply', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: this.user.user_id, drive_id: driveId })
      });
      if(res.ok) this.loadDashboard();
      else { const d = await res.json(); alert(d.message); }
    },
    async triggerExport() {
      const res = await fetch('/api/student/export', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ student_id: this.user.user_id })
      });
      const d = await res.json(); alert(d.message);
    },
    handleFileUpload(e) {
      this.resumeFile = e.target.files[0];
    },
    async updateProfile() {
      const formData = new FormData();
      formData.append('student_id', this.user.user_id);
      if(this.profileForm.cgpa) formData.append('cgpa', this.profileForm.cgpa);
      if(this.profileForm.branch) formData.append('branch', this.profileForm.branch);
      if(this.resumeFile) formData.append('resume', this.resumeFile);
      
      const res = await fetch('/api/student/profile', { method: 'POST', body: formData });
      const d = await res.json();
      alert(d.message);
      this.loadDashboard();
    },
    logout() { this.$emit('logout'); }
  }
}
  </script>