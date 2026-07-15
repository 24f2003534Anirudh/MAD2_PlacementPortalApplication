<template>
  <div class="auth-wrapper">
  <div>
      <div class="text-center mb-4">
        <h3 class="fw-bold">Create Account</h3>
        <p class="text-muted small">Register a new account</p>
      </div>

      <div v-if="errorMsg" class="alert alert-danger py-2 px-3 small mb-3" role="alert">
        {{ errorMsg }}
      </div>

      <div v-if="successMsg" class="alert alert-success py-2 px-3 small mb-3" role="alert">
        {{ successMsg }}
      </div>

      <form v-if="!successMsg" @submit.prevent="register">
        <div class="btn-group w-100 mb-3" role="group">
          <button 
            type="button" 
            class="btn" 
            :class="form.role === 'student' ? 'btn-dark' : 'btn-outline-dark'"
            @click="form.role = 'student'"
          >
            Student
          </button>
          <button 
            type="button" 
            class="btn" 
            :class="form.role === 'company' ? 'btn-dark' : 'btn-outline-dark'"
            @click="form.role = 'company'"
          >
            Company
          </button>
        </div>
        <div class="row">
          <div class="col-md-6 mb-3">
            <label for="reg-username" class="form-label small fw-semibold">Email</label>
            <input 
              type="text" 
              class="form-control" 
              id="reg-username" 
              v-model="form.username" 
              required
            >
          </div>
          <div class="col-md-6 mb-3">
            <label for="reg-password" class="form-label small fw-semibold">Password</label>
            <input 
              type="password" 
              class="form-control" 
              id="reg-password" 
              v-model="form.password" 
              required
            >
          </div>
        </div>
        <div v-if="form.role === 'student'">
          <div class="row">
            <div class="col-md-4 mb-3">
              <label for="cgpa" class="form-label small fw-semibold">CGPA</label>
              <input 
                type="number" 
                step="0.01" 
                min="0" 
                max="10" 
                class="form-control" 
                id="cgpa" 
                v-model="form.cgpa" 
                required
              >
            </div>
            <div class="col-md-4 mb-3">
              <label for="branch" class="form-label small fw-semibold">Branch</label>
              <input 
                type="text" 
                class="form-control" 
                id="branch" 
                v-model="form.branch" 
                required
              >
            </div>
            <div class="col-md-4 mb-3">
              <label for="year" class="form-label small fw-semibold">Graduation Year</label>
              <input 
                type="number" 
                min="2000" 
                max="2100" 
                class="form-control" 
                id="year" 
                v-model="form.year" 
                required
              >
            </div>
          </div>
        </div>
        <div v-if="form.role === 'company'">
          <div class="mb-3">
            <label for="company_name" class="form-label small fw-semibold">Company Name</label>
            <input 
              type="text" 
              class="form-control" 
              id="company_name" 
              v-model="form.company_name" 
              required
            >
          </div>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="hr_contact" class="form-label small fw-semibold">HR Contact</label>
              <input 
                type="text" 
                class="form-control" 
                id="hr_contact" 
                v-model="form.hr_contact" 
                required
              >
            </div>
            <div class="col-md-6 mb-3">
              <label for="website" class="form-label small fw-semibold">Website</label>
              <input 
                type="url" 
                class="form-control" 
                id="website" 
                v-model="form.website" 
                required
              >
            </div>
          </div>
        </div>

        <button type="submit" class="btn btn-custom w-100 mb-3" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
          Register
        </button>

        <div class="text-center small text-muted">
          Already have an account? 
          <a href="#" @click.prevent="$emit('change-view', 'login')" class="text-primary text-decoration-none">Sign In</a>
        </div>
      </form>
      <div v-else class="text-center">
        <p class="mb-4">
          {{ form.role === 'company' 
            ? 'Registration submitted. Awaiting Admin approval.' 
            : 'Registration complete. You can now log in.' }}
        </p>
        <button @click="$emit('change-view', 'login')" class="btn btn-custom w-100">
          Go to Sign In
        </button>
      </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: '',
        password: '',
        role: 'student',
        cgpa: '',
        branch: '',
        year: 2026,
        company_name: '',
        hr_contact: '',
        website: ''
      },
      errorMsg: '',
      successMsg: '',
      loading: false
    }
  },
  methods: {
    async register() {
      this.errorMsg = '';
      this.successMsg = '';
      
      if (this.form.role === 'student') {
        const parsedCGPA = parseFloat(this.form.cgpa);
        if (isNaN(parsedCGPA) || parsedCGPA < 0 || parsedCGPA > 10) {
          this.errorMsg = 'CGPA must be a decimal between 0.00 and 10.00';
          return;
        }
      }

      this.loading = true;
      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.form)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.message || 'Registration failed.');
        }
        
        this.successMsg = 'Registration completed successfully!';
      } catch (err) {
        this.errorMsg = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
