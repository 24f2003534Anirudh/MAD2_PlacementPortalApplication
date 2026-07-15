<template>
  <div>
<!-- company navbar -->
    <nav class="navbar navbar-expand navbar-dark bg-dark px-3">
      <div class="container-fluid">
        <span class="navbar-brand fw-bold">Company</span>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <a class="nav-link" :class="{ active: currentTab === 'profile' }" href="#" @click.prevent="currentTab = 'profile'">Profile</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" :class="{ active: currentTab === 'drives' }" href="#" @click.prevent="currentTab = 'drives'">Make Drive</a>
            </li>
          </ul>
          <div class="d-flex align-items-center text-light me-3">
            <span class="small me-3">{{ user.username }} (Status: {{ user.status }})</span>
            <button @click="$emit('logout')" class="btn btn-sm btn-danger">Log Out</button>
          </div>
        </div>
      </div>
    </nav>
<!-- page body -->
    <div class="container py-4">
      <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
        <h4 class="fw-bold m-0 text-capitalize">{{ currentTab === 'profile' ? 'Profile & Overview' : 'Create New Drive' }}</h4>
      </div>

      <div v-if="alertMsg" class="alert alert-secondary py-2 px-3 small mb-4">
        {{ alertMsg }}
      </div>
<!-- profile and applications tab -->
      <div v-if="currentTab === 'profile'">
        <div v-if="user.status !== 'Approved'" class="alert alert-warning small mb-4">
          <strong>Profile Awaiting Approval:</strong> Your account is pending verification. You can view placement history but cannot publish new recruitment drives yet.
        </div>

        <div class="simple-card mb-4">
          <h5 class="fw-bold mb-3">Corporate Profile Overview</h5>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label class="text-muted small fw-semibold d-block">Username</label>
              <span>{{ user.username }}</span>
            </div>
            <div class="col-md-6 mb-3">
              <label class="text-muted small fw-semibold d-block">Account ID</label>
              <span>#{{ user.user_id }}</span>
            </div>
          </div>
        </div>

        <div class="simple-card mb-4">
          <h5 class="fw-bold mb-3">Drives Made</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-striped align-middle">
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>Criteria</th>
                  <th>Deadline</th>
                  <th>Applicants</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in drives" :key="d.id">
                  <td class="fw-bold">{{ d.job_title }}</td>
                  <td>CGPA: {{ d.min_cgpa }} | Branch: {{ d.branch_criteria }}</td>
                  <td>{{ d.application_deadline || 'N/A' }}</td>
                  <td>{{ d.applicants }} applied</td>
                  <td>{{ d.status }}</td>
                </tr>
                <tr v-if="drives.length === 0">
                  <td colspan="5" class="text-center text-muted py-3">No drives created.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="simple-card">
          <h5 class="fw-bold mb-3">Student Applications</h5>
          <div class="table-responsive">
            <table class="table table-bordered table-striped align-middle">
              <thead>
                <tr>
                  <th>Student Name</th>
                  <th>Job Role</th>
                  <th>Resume</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in apps" :key="a.id">
                  <td>
                    <span class="fw-bold d-block">{{ a.student_name }}</span>
                    <span class="small text-muted">CGPA: {{ a.student_cgpa }} | Branch: {{ a.student_branch }}</span>
                  </td>
                  <td class="fw-bold">{{ a.job_title }}</td>
                  <td>
                    <a v-if="a.resume_url" :href="a.resume_url" target="_blank">View Resume</a>
                    <span v-else class="text-muted small">None</span>
                  </td>
                  <td>{{ a.status }}</td>
                  <td>
                    <div v-if="a.status === 'Applied'" class="btn-group btn-group-sm">
                      <button @click="updateAppStatus(a.id, 'Shortlisted')" class="btn btn-warning text-dark btn-sm">Shortlist</button>
                      <button @click="updateAppStatus(a.id, 'Rejected')" class="btn btn-outline-danger btn-sm">Reject</button>
                    </div>
                    <div v-else-if="a.status === 'Shortlisted'" class="btn-group btn-group-sm">
                      <button @click="updateAppStatus(a.id, 'Selected')" class="btn btn-success btn-sm">Select Student</button>
                      <button @click="updateAppStatus(a.id, 'Rejected')" class="btn btn-outline-danger btn-sm">Reject</button>
                    </div>
                    <div v-else-if="a.status === 'Selected'">
                      <span class="text-muted small">Selected</span>
                    </div>
                    <span v-else class="text-muted small">Closed</span>
                  </td>
                </tr>
                <tr v-if="apps.length === 0">
                  <td colspan="5" class="text-center text-muted py-3">No applications.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
<!-- drives tab -->
      <div v-if="currentTab === 'drives'">
        <div class="row g-4 justify-content-center">
          <div class="col-lg-6" v-if="user.status === 'Approved'">
            <div class="simple-card">
              <h5 class="fw-bold mb-3">Create Placement Drive</h5>
              <form @submit.prevent="createDrive">
                <div class="mb-3">
                  <label for="job-title" class="form-label small fw-semibold">Job Title</label>
                  <input type="text" class="form-control" id="job-title" v-model="driveForm.job_title" required>
                </div>
                <div class="mb-3">
                  <label for="job-desc" class="form-label small fw-semibold">Job Description</label>
                  <textarea class="form-control" id="job-desc" rows="3" v-model="driveForm.job_description" required></textarea>
                </div>
                <div class="row">
                  <div class="col-6 mb-3">
                    <label for="min-cgpa" class="form-label small fw-semibold">Min CGPA</label>
                    <input type="number" step="0.1" min="0" max="10" class="form-control" id="min-cgpa" v-model="driveForm.min_cgpa" required>
                  </div>
                  <div class="col-6 mb-3">
                    <label for="branch-crit" class="form-label small fw-semibold">Eligible Branch</label>
                    <input type="text" class="form-control" id="branch-crit" v-model="driveForm.branch_criteria" required>
                  </div>
                </div>
                <div class="mb-4">
                  <label for="deadline" class="form-label small fw-semibold">Application Deadline</label>
                  <input type="date" class="form-control" id="deadline" v-model="driveForm.application_deadline" required>
                </div>
                <button type="submit" class="btn btn-custom w-100" :disabled="driveLoading">
                  <span v-if="driveLoading" class="spinner-border spinner-border-sm me-1"></span>
                  Publish Drive
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  props: ['user'],
  data() {
    return {
      currentTab: 'profile',
      drives: [],
      apps: [],
      alertMsg: '',
      driveForm: {
        job_title: '',
        job_description: '',
        min_cgpa: '',
        branch_criteria: '',
        application_deadline: ''
      },
      driveLoading: false
    }
  },
  methods: {
    async fetchDrives() {
      try {
        const res = await fetch(`/api/company/drives?company_id=${this.user.user_id}`);
        const data = await res.json();
        this.drives = data;
      } catch (e) {
        console.error(e);
      }
    },
    async fetchApps() {
      try {
        const res = await fetch(`/api/company/applications?company_id=${this.user.user_id}`);
        const data = await res.json();
        this.apps = data;
      } catch (e) {
        console.error(e);
      }
    },
    async createDrive() {
      this.driveLoading = true;
      try {
        const res = await fetch('/api/company/drives', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company_id: this.user.user_id,
            ...this.driveForm
          })
        });
        const data = await res.json();
        if (res.ok) {
          this.alertMsg = data.message;
          this.fetchDrives();
          this.driveForm = { job_title: '', job_description: '', min_cgpa: '', branch_criteria: '', application_deadline: '' };
        } else {
          this.alertMsg = `Error: ${data.message}`;
        }
      } catch (e) {
        console.error(e);
      } finally {
        this.driveLoading = false;
      }
    },
    async updateAppStatus(appId, status) {
      let interviewDate = null;
      if (status === 'Shortlisted') {
        const inputVal = prompt("Enter interview date/time (e.g., 2026-07-20 14:30) or leave blank:");
        if (inputVal === null) return;
        interviewDate = inputVal.trim() || null;
      }
      try {
        const res = await fetch(`/api/company/applications/${appId}/status`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status, interview_date: interviewDate })
        });
        if (res.ok) {
          this.alertMsg = `Application status updated to ${status}.`;
          this.fetchApps();
        }
      } catch (e) {
        console.error(e);
      }
    },

    fetchData() {
      this.fetchDrives();
      this.fetchApps();
    }
  },
  created() {
    this.fetchData();
  }
}
</script>
