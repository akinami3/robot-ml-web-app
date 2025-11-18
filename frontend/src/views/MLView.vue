<template>
  <div class="ml-view">
    <div class="view-header">
      <h1>Machine Learning</h1>
      <p class="subtitle">Train and manage machine learning models</p>
    </div>

    <div class="ml-grid">
      <!-- Training Chart -->
      <div class="chart-section">
        <TrainingChart
          :metrics="trainingMetrics"
          :isTraining="isTraining"
          :currentEpoch="currentEpoch"
          :totalEpochs="totalEpochs"
        />
      </div>

      <!-- Training Controls -->
      <div class="controls-panel">
        <h2>Training Configuration</h2>
        
        <form v-if="!isTraining" @submit.prevent="handleStartTraining" class="training-form">
          <div class="form-group">
            <label>Model</label>
            <select v-model="selectedModelId" class="input" required>
              <option value="">Select a model</option>
              <option v-for="model in models" :key="model.id" :value="model.id">
                {{ model.name }} ({{ model.model_type }})
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Dataset ID</label>
            <input v-model="trainingConfig.dataset_id" type="text" class="input" placeholder="Enter dataset ID" required />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Epochs</label>
              <input v-model.number="trainingConfig.epochs" type="number" min="1" class="input" required />
            </div>
            <div class="form-group">
              <label>Batch Size</label>
              <input v-model.number="trainingConfig.batch_size" type="number" min="1" class="input" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Learning Rate</label>
              <input v-model.number="trainingConfig.learning_rate" type="number" step="0.0001" class="input" />
            </div>
            <div class="form-group">
              <label>Device</label>
              <select v-model="trainingConfig.device" class="input">
                <option value="cpu">CPU</option>
                <option value="cuda">CUDA (GPU)</option>
              </select>
            </div>
          </div>

          <button type="submit" class="btn btn-primary btn-large" :disabled="!selectedModelId">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Start Training
          </button>
        </form>

        <div v-else class="training-active">
          <div class="progress-info">
            <h3>Training in Progress</h3>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <p class="progress-text">Epoch {{ currentEpoch }} / {{ totalEpochs }} ({{ progressPercent }}%)</p>
          </div>
          
          <button @click="handleStopTraining" class="btn btn-danger btn-large">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
            Stop Training
          </button>
        </div>
      </div>

      <!-- Models List -->
      <div class="models-panel">
        <div class="panel-header">
          <h2>Models</h2>
          <button @click="showCreateModel = true" class="btn-create">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            New Model
          </button>
        </div>

        <div class="models-list">
          <div v-for="model in models" :key="model.id" class="model-card">
            <div class="model-header">
              <h3>{{ model.name }}</h3>
              <span class="model-status" :class="`status-${model.status}`">
                {{ model.status }}
              </span>
            </div>
            <div class="model-info">
              <span class="info-label">Type:</span>
              <span>{{ model.model_type }}</span>
            </div>
            <div v-if="model.architecture" class="model-info">
              <span class="info-label">Architecture:</span>
              <span>{{ model.architecture }}</span>
            </div>
            <div class="model-actions">
              <button @click="selectModel(model.id)" class="btn-select">Select</button>
              <button @click="handleDeleteModel(model.id)" class="btn-delete">Delete</button>
            </div>
          </div>

          <div v-if="models.length === 0" class="empty-models">
            <p>No models created yet</p>
            <button @click="showCreateModel = true" class="btn-create-first">
              Create your first model
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Model Modal -->
    <div v-if="showCreateModel" class="modal-overlay" @click="showCreateModel = false">
      <div class="modal-content" @click.stop>
        <h2>Create New Model</h2>
        <form @submit.prevent="handleCreateModel" class="modal-form">
          <div class="form-group">
            <label>Model Name</label>
            <input v-model="newModel.name" type="text" class="input" required />
          </div>
          <div class="form-group">
            <label>Model Type</label>
            <select v-model="newModel.model_type" class="input" required>
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
              <option value="detection">Object Detection</option>
            </select>
          </div>
          <div class="form-group">
            <label>Architecture (Optional)</label>
            <input v-model="newModel.architecture" type="text" class="input" placeholder="e.g., ResNet50, CNN" />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showCreateModel = false" class="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMLTraining } from '@/composables/useMLTraining'
import TrainingChart from '@/components/ml/TrainingChart.vue'

const {
  models,
  trainingMetrics,
  isTraining,
  currentEpoch,
  totalEpochs,
  fetchModels,
  createModel,
  deleteModel,
  startTraining,
  stopTraining,
} = useMLTraining()

const selectedModelId = ref('')
const showCreateModel = ref(false)

const trainingConfig = ref({
  dataset_id: '',
  epochs: 100,
  batch_size: 32,
  learning_rate: 0.001,
  device: 'cpu',
  early_stopping_patience: 10,
})

const newModel = ref({
  name: '',
  model_type: 'classification',
  architecture: '',
})

const progressPercent = computed(() => {
  if (totalEpochs.value === 0) return 0
  return Math.round((currentEpoch.value / totalEpochs.value) * 100)
})

const selectModel = (modelId: string) => {
  selectedModelId.value = modelId
}

const handleStartTraining = async () => {
  if (!selectedModelId.value) return

  try {
    await startTraining(selectedModelId.value, trainingConfig.value)
  } catch (error) {
    alert('Failed to start training')
  }
}

const handleStopTraining = async () => {
  if (!selectedModelId.value) return

  try {
    await stopTraining(selectedModelId.value)
  } catch (error) {
    alert('Failed to stop training')
  }
}

const handleCreateModel = async () => {
  try {
    await createModel(newModel.value)
    showCreateModel.value = false
    newModel.value = {
      name: '',
      model_type: 'classification',
      architecture: '',
    }
  } catch (error) {
    alert('Failed to create model')
  }
}

const handleDeleteModel = async (modelId: string) => {
  if (!confirm('Are you sure you want to delete this model?')) return

  try {
    await deleteModel(modelId)
  } catch (error) {
    alert('Failed to delete model')
  }
}
</script>

<style scoped>
.ml-view {
  padding: 2rem;
}

.view-header {
  margin-bottom: 2rem;
}

.view-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  color: #1f2937;
}

.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 1rem;
}

.ml-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 1280px) {
  .ml-grid {
    grid-template-columns: 1fr;
  }
}

.chart-section {
  grid-column: 1 / -1;
}

.controls-panel,
.models-panel {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}

.controls-panel h2,
.models-panel h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.125rem;
  color: #1f2937;
}

.training-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-large {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  margin-top: 0.5rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.icon {
  width: 1.25rem;
  height: 1.25rem;
}

.training-active {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.progress-info h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #1f2937;
}

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  transition: width 0.3s ease;
}

.progress-text {
  margin: 0.5rem 0 0 0;
  font-size: 0.875rem;
  color: #6b7280;
  text-align: center;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create:hover {
  background: #f9fafb;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 500px;
  overflow-y: auto;
}

.model-card {
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.75rem;
}

.model-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
}

.model-status {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-idle {
  background: #f3f4f6;
  color: #6b7280;
}

.status-training {
  background: #dbeafe;
  color: #1e40af;
}

.status-trained {
  background: #d1fae5;
  color: #065f46;
}

.model-info {
  display: flex;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.info-label {
  font-weight: 500;
  color: #374151;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-select,
.btn-delete {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-select:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #3b82f6;
}

.btn-delete:hover {
  background: #fef2f2;
  border-color: #ef4444;
  color: #ef4444;
}

.empty-models {
  padding: 3rem 1rem;
  text-align: center;
  color: #9ca3af;
}

.btn-create-first {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  border-radius: 0.375rem;
  background: #3b82f6;
  color: white;
  font-size: 0.875rem;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15);
}

.modal-content h2 {
  margin: 0 0 1.5rem 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1rem;
}
</style>
