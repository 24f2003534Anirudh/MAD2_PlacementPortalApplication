<template>
  <div class="auth-wrapper">
  <div>
      <div class="text-center mb-4">
        <h3 class="fw-bold">Placement Portal</h3>
        <p class="text-muted small">Sign in</p>
      </div>

      <div v-if="errorMsg" class="alert alert-danger py-2 px-3 small mb-3" role="alert">
        {{ errorMsg }}
      </div>

      <form @submit.prevent="login">
        <div class="mb-3">
          <label for="username" class="form-label small fw-semibold">Email</label>
          <input 
            type="text" 
            class="form-control" 
            id="username" 
            v-model="form.username" 
            required
          >
        </div>

        <div class="mb-4">
          <label for="password" class="form-label small fw-semibold">Password</label>
          <input 
            type="password" 
            class="form-control" 
            id="password" 
            v-model="form.password" 
            required
          >
        </div>

        <button type="submit" class="btn btn-custom w-100 mb-3" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          Sign In
        </button>

        <div class="text-center small text-muted">
          <a href="#" @click.prevent="$emit('change-view', 'register')" class="text-primary text-decoration-none">Register</a>
        </div>
      </form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      errorMsg: '',
      loading: false
    }
  },
  methods: {
    async login() {
      this.errorMsg = '';
      this.loading = true;
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.form)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.message || 'Login failed.');
        }
        
        this.$emit('login-success', data);
      } catch (err) {
        this.errorMsg = err.message;
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>
