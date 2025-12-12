# 🚀 A2A TASK UI IMPROVEMENTS - IMPLEMENTATION ROADMAP

**Status:** Ready for Execution  
**Timeline:** 4 Weeks  
**Team Size:** 2-3 Full-Stack Engineers  
**Effort:** ~160-200 hours  

---

## 📊 EXECUTIVE SUMMARY

### What We're Building
A complete overhaul of the task creation, progress tracking, and results delivery experience with:
- ✅ 3-step intelligent task creation wizard
- ✅ Rich real-time progress dashboard with live updates
- ✅ Detailed task view with timeline visualization
- ✅ Execution plan review & approval workflow
- ✅ Structured results delivery with metrics
- ✅ User feedback collection for continuous improvement

### Business Value
| Metric | Current | Improved | Impact |
|--------|---------|----------|--------|
| Task Creation Time | 3 min | 8 min (but better) | Better guidance |
| User Clarity | 40% understand flow | 95% understand | Reduced errors |
| Error Recovery | Manual | 1-click retry | User satisfaction |
| Results Actionability | 30% | 90% | Higher adoption |
| Agent Performance Visibility | 0% | 100% | Better optimization |

### Risk Assessment
**Risk Level:** 🟡 MEDIUM (but mitigable)
- **Pro:** Pure frontend + minimal backend changes
- **Con:** 15+ new components to coordinate
- **Mitigation:** Feature flags for gradual rollout

---

## 🗓️ WEEK 1: TASK CREATION WIZARD & DATABASE ENHANCEMENTS

### Sprint Goal
Implement the 3-step task creation wizard with intelligent recommendations and database tracking.

### Backend Tasks (2-3 days)

#### 1.1 Database Schema Updates
**File:** `backend/alembic/versions/001_enhance_tasks_table.py`

```python
# Add columns to tasks table
ALTER TABLE tasks ADD COLUMN (
    current_phase VARCHAR DEFAULT 'created',  -- 'created', 'planning', 'delegating', 'executing', 'completed'
    current_agent_type VARCHAR,
    current_agent_ve_id VARCHAR,
    execution_plan JSONB,
    plan_approved_at TIMESTAMP,
    plan_approved_by UUID REFERENCES auth.users(id),
    quality_score INT CHECK (quality_score >= 0 AND quality_score <= 100),
    estimated_duration_minutes INT,
    actual_duration_minutes INT,
    result_summary TEXT,
    result_details JSONB,
    user_feedback JSONB,  -- {rating: 1-5, comments: string, tags: [string]}
    created_at TIMESTAMP DEFAULT NOW()
);

# Create indexes
CREATE INDEX idx_tasks_customer_phase ON tasks(customer_id, current_phase);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

**Checklist:**
- [ ] Write migration file
- [ ] Test migration on staging DB
- [ ] Verify backward compatibility
- [ ] Document schema changes

#### 1.2 New Task Events Table
**File:** `backend/alembic/versions/002_create_task_events_table.py`

```python
# Create comprehensive task event tracking
CREATE TABLE task_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    customer_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,  -- 'created', 'status_change', 'plan_generated', 'approved', 'delegated', 'completed', 'error'
    event_data JSONB NOT NULL,  -- Flexible structure for different events
    agent_type VARCHAR,  -- Which agent created this event
    agent_ve_id VARCHAR,
    triggered_by VARCHAR,  -- 'user', 'system', 'agent'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_events_task ON task_events(task_id, created_at DESC);
CREATE INDEX idx_task_events_customer ON task_events(customer_id, created_at DESC);
CREATE INDEX idx_task_events_type ON task_events(event_type, created_at DESC);
```

**Checklist:**
- [ ] Create migration
- [ ] Add event logging helper functions
- [ ] Create task_timeline view
- [ ] Test query performance

#### 1.3 API Endpoint: Enhanced Task Creation
**File:** `backend/app/routes/tasks.py`

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.db.supabase import SupabaseClient
from app.temporal.workflows import OrchestratorWorkflow

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreationStep1(BaseModel):
    """Context step: What needs to be done?"""
    title: str
    description: str
    requirements: list[str] = []

class TaskCreationStep2(BaseModel):
    """Requirements step: When, how urgent, what approach?"""
    due_date: datetime
    priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_duration: str  # '<2h', '<1d', '2-3d', '>1w'
    preferred_approach: list[str]  # ['coordinate', 'specialist', 'parallel', 'approval']
    business_impact: str

class TaskCreationFull(BaseModel):
    """Complete task creation payload"""
    step1: TaskCreationStep1
    step2: TaskCreationStep2

@router.post("/create-wizard")
async def create_task_via_wizard(
    payload: TaskCreationFull,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    Create task with full wizard context.
    Returns task with AI-generated recommendations.
    """
    
    customer_id = user.customer_id
    
    # 1. Create task record
    task = db.table('tasks').insert({
        'customer_id': customer_id,
        'title': payload.step1.title,
        'description': payload.step1.description,
        'priority': payload.step2.priority,
        'due_date': payload.step2.due_date,
        'estimated_duration_minutes': parse_duration(payload.step2.estimated_duration),
        'current_phase': 'created',
        'created_at': datetime.now(timezone.utc)
    }).execute()
    
    task_id = task.data[0]['id']
    
    # 2. Log creation event
    db.table('task_events').insert({
        'task_id': task_id,
        'customer_id': customer_id,
        'event_type': 'created',
        'event_data': {
            'title': payload.step1.title,
            'priority': payload.step2.priority
        },
        'triggered_by': 'user'
    }).execute()
    
    # 3. Generate AI recommendations
    recommendations = await generate_task_recommendations(
        title=payload.step1.title,
        description=payload.step1.description,
        priority=payload.step2.priority,
        duration=payload.step2.estimated_duration,
        approach_preferences=payload.step2.preferred_approach
    )
    
    # 4. Start workflow in background
    background_tasks.add_task(
        start_orchestrator_workflow,
        task_id=task_id,
        customer_id=customer_id,
        recommendations=recommendations
    )
    
    return {
        'task_id': task_id,
        'status': 'created',
        'phase': 'created',
        'recommendations': recommendations,
        'message': 'Task created. Workflow starting...'
    }

@router.get("/recommendations/{task_id}")
async def get_task_recommendations(
    task_id: str,
    user = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    Get AI-generated recommendations for task execution.
    Called from Step 3 review screen.
    """
    task = db.table('tasks').select('*').eq('id', task_id).single().execute()
    
    if task.data['customer_id'] != user.customer_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Generate recommendations based on task context
    recs = await generate_task_recommendations(
        title=task.data['title'],
        description=task.data['description'],
        priority=task.data['priority'],
        customer_id=user.customer_id  # Pass customer context
    )
    
    return recs
```

**Checklist:**
- [ ] Implement endpoint
- [ ] Add input validation
- [ ] Write unit tests
- [ ] Add error handling
- [ ] Document API

#### 1.4 Recommendation Engine
**File:** `backend/app/services/recommendations.py`

```python
import anthropic
from app.models import Task

async def generate_task_recommendations(title: str, description: str, priority: str, customer_id: str, duration: str = None):
    """
    Use Claude to generate intelligent task execution recommendations.
    """
    client = anthropic.Anthropic()
    
    prompt = f"""
    You are an AI task orchestration expert. Based on the following task details, 
    provide recommendations for how this task should be executed.
    
    Task Title: {title}
    Description: {description}
    Priority: {priority}
    Estimated Duration: {duration or 'not specified'}
    
    Generate a JSON response with:
    {{
        "execution_approach": "manager_coordinates" | "specialist_directly" | "parallel_execution" | "requires_clarification",
        "confidence": 0.0-1.0,
        "reasoning": "2-3 sentence explanation",
        "estimated_steps": 3-5,
        "resource_hints": ["list", "of", "needed", "skills"],
        "risk_factors": ["list", "of", "potential", "issues"],
        "success_criteria": "clear description of what success looks like"
    }}
    
    Be concise and practical.
    """
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse response
    response_text = message.content[0].text
    recommendations = json.loads(response_text)
    
    return recommendations
```

**Checklist:**
- [ ] Integrate with Claude API
- [ ] Add error handling & retries
- [ ] Cache recommendations
- [ ] Add logging

### Frontend Tasks (2-3 days)

#### 1.5 Task Creation Wizard Component
**File:** `frontend/src/components/TaskCreationWizard.tsx`

```typescript
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Step1Context } from './wizard/Step1Context';
import { Step2Requirements } from './wizard/Step2Requirements';
import { Step3Review } from './wizard/Step3Review';

type WizardStep = 1 | 2 | 3;

interface WizardState {
  step: WizardStep;
  step1: any;
  step2: any;
  recommendations: any | null;
  isLoading: boolean;
  error: string | null;
}

export const TaskCreationWizard: React.FC<{ onComplete: (taskId: string) => void }> = ({ onComplete }) => {
  const [state, setState] = useState<WizardState>({
    step: 1,
    step1: null,
    step2: null,
    recommendations: null,
    isLoading: false,
    error: null
  });

  const handleStep1Submit = async (data) => {
    setState(prev => ({ ...prev, step1: data, step: 2 }));
  };

  const handleStep2Submit = async (data) => {
    setState(prev => ({ ...prev, step2: data, isLoading: true }));
    
    try {
      // Get recommendations from API
      const response = await fetch('/api/tasks/create-wizard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step1: state.step1,
          step2: data
        })
      });
      
      if (!response.ok) throw new Error('Failed to create task');
      
      const result = await response.json();
      
      setState(prev => ({
        ...prev,
        recommendations: result.recommendations,
        step: 3,
        isLoading: false
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
    }
  };

  const handleStep3Confirm = async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    
    try {
      // API already created task in step 2
      // Just confirm and navigate
      onComplete(state.recommendations.task_id);
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
    }
  };

  return (
    <div className="wizard-container">
      <AnimatePresence mode="wait">
        {state.step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Step1Context onSubmit={handleStep1Submit} />
          </motion.div>
        )}
        
        {state.step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Step2Requirements 
              onSubmit={handleStep2Submit}
              isLoading={state.isLoading}
            />
          </motion.div>
        )}
        
        {state.step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <Step3Review 
              recommendations={state.recommendations}
              onConfirm={handleStep3Confirm}
              isLoading={state.isLoading}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
```

**Checklist:**
- [ ] Create Step1Context component
- [ ] Create Step2Requirements component
- [ ] Create Step3Review component
- [ ] Implement navigation logic
- [ ] Add error boundaries
- [ ] Style with Tailwind
- [ ] Test animations

#### 1.6 Step 1: Context Capture
**File:** `frontend/src/components/wizard/Step1Context.tsx`

```typescript
import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface Step1Props {
  onSubmit: (data: any) => void;
}

export const Step1Context: React.FC<Step1Props> = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    requirements: []
  });

  const [currentRequirement, setCurrentRequirement] = useState('');
  const [charCount, setCharCount] = useState(0);

  const handleDescriptionChange = (e) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, description: value }));
    setCharCount(value.length);
  };

  const addRequirement = () => {
    if (currentRequirement.trim()) {
      setFormData(prev => ({
        ...prev,
        requirements: [...prev.requirements, currentRequirement]
      }));
      setCurrentRequirement('');
    }
  };

  const removeRequirement = (index: number) => {
    setFormData(prev => ({
      ...prev,
      requirements: prev.requirements.filter((_, i) => i !== index)
    }));
  };

  const isValid = formData.title.length > 5 && formData.description.length > 20;

  return (
    <div className="space-y-6 p-6 bg-white rounded-lg">
      <div>
        <h2 className="text-2xl font-semibold mb-2">📋 What needs to be done?</h2>
        <p className="text-gray-600 text-sm">Be specific to get better recommendations</p>
      </div>

      {/* Title Input */}
      <div>
        <label className="block text-sm font-medium mb-2">Task Title</label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
          placeholder="e.g., 'Design landing page for Q1 launch'"
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">💡 Be specific, not generic</p>
      </div>

      {/* Description Input */}
      <div>
        <label className="block text-sm font-medium mb-2">Description (detailed context)</label>
        <textarea
          value={formData.description}
          onChange={handleDescriptionChange}
          placeholder="Describe what needs to be done, any specific requirements, context, or constraints..."
          rows={6}
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>The more detail, the better the plan</span>
          <span>{charCount}/5000</span>
        </div>
      </div>

      {/* Requirements Input */}
      <div>
        <label className="block text-sm font-medium mb-2">Key Requirements (optional)</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={currentRequirement}
            onChange={(e) => setCurrentRequirement(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addRequirement()}
            placeholder="Add requirement and press Enter"
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button
            onClick={addRequirement}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Add
          </button>
        </div>
        
        {formData.requirements.length > 0 && (
          <div className="mt-3 space-y-2">
            {formData.requirements.map((req, idx) => (
              <div key={idx} className="flex items-center justify-between bg-blue-50 p-2 rounded">
                <span className="text-sm">{req}</span>
                <button
                  onClick={() => removeRequirement(idx)}
                  className="text-red-500 hover:text-red-700"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-end pt-4">
        <button className="px-6 py-2 border rounded-lg hover:bg-gray-50">Cancel</button>
        <button
          onClick={() => onSubmit(formData)}
          disabled={!isValid}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next <ChevronDown className="inline ml-2" />
        </button>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Implement form state
- [ ] Add validation
- [ ] Style with design system
- [ ] Test character counter
- [ ] Add keyboard shortcuts

#### 1.7 Step 2: Requirements & Preferences
**File:** `frontend/src/components/wizard/Step2Requirements.tsx`

```typescript
import React, { useState } from 'react';

interface Step2Props {
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

export const Step2Requirements: React.FC<Step2Props> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState({
    dueDate: '',
    dueTime: '23:59',
    priority: 'medium',
    estimatedDuration: '<1d',
    businessImpact: '',
    preferredApproach: {
      needsCoordinator: false,
      needsSpecialist: false,
      parallelWork: false,
      needsApproval: false
    }
  });

  const [urgencyWarning, setUrgencyWarning] = useState('');

  const handleDueDateChange = (date: string) => {
    const daysUntil = Math.ceil((new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    
    if (daysUntil < 1) {
      setUrgencyWarning('⚠️ Very urgent - tight timeline');
    } else if (daysUntil < 3) {
      setUrgencyWarning('⚠️ 3 days or less - tight deadline');
    } else {
      setUrgencyWarning('');
    }
    
    setFormData(prev => ({ ...prev, dueDate: date }));
  };

  const priorityOptions = [
    { value: 'low', label: 'Low (Nice to have)', icon: '🟢' },
    { value: 'medium', label: 'Medium (Standard)', icon: '🟡' },
    { value: 'high', label: 'High (Urgent)', icon: '🔴' },
    { value: 'critical', label: 'Critical (Blocking)', icon: '⛔' }
  ];

  const durationOptions = [
    { value: '<2h', label: '< 2 hours' },
    { value: '<1d', label: '< 1 day' },
    { value: '2-3d', label: '2-3 days' },
    { value: '>1w', label: '> 1 week' }
  ];

  const isValid = formData.dueDate && formData.businessImpact.length > 10;

  return (
    <div className="space-y-6 p-6 bg-white rounded-lg">
      <div>
        <h2 className="text-2xl font-semibold mb-2">⏰ Requirements & Timeline</h2>
        <p className="text-gray-600 text-sm">Help us understand your constraints</p>
      </div>

      {/* Timeline Section */}
      <div className="border-t pt-4">
        <h3 className="font-semibold mb-4">📅 TIMELINE</h3>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">Due Date</label>
            <input
              type="date"
              value={formData.dueDate}
              onChange={(e) => handleDueDateChange(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Due Time</label>
            <input
              type="time"
              value={formData.dueTime}
              onChange={(e) => setFormData(prev => ({ ...prev, dueTime: e.target.value }))}
              className="w-full px-4 py-2 border rounded-lg"
            />
          </div>
        </div>
        
        {urgencyWarning && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
            {urgencyWarning}
          </div>
        )}
        
        <div className="mt-4">
          <label className="block text-sm font-medium mb-3">Expected Duration</label>
          <div className="grid grid-cols-2 gap-3">
            {durationOptions.map(opt => (
              <button
                key={opt.value}
                onClick={() => setFormData(prev => ({ ...prev, estimatedDuration: opt.value }))}
                className={`p-3 border rounded-lg text-left transition ${
                  formData.estimatedDuration === opt.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input type="radio" className="mr-2" checked={formData.estimatedDuration === opt.value} readOnly />
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Priority Section */}
      <div className="border-t pt-4">
        <h3 className="font-semibold mb-4">⭐ PRIORITY</h3>
        
        <label className="block text-sm font-medium mb-3">Priority Level</label>
        <div className="grid grid-cols-2 gap-3">
          {priorityOptions.map(opt => (
            <button
              key={opt.value}
              onClick={() => setFormData(prev => ({ ...prev, priority: opt.value }))}
              className={`p-3 border rounded-lg text-left transition ${
                formData.priority === opt.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="flex items-center">
                <input type="radio" className="mr-2" checked={formData.priority === opt.value} readOnly />
                <span>{opt.icon}</span>
              </div>
              <div className="text-sm">{opt.label}</div>
            </button>
          ))}
        </div>
        
        <div className="mt-4">
          <label className="block text-sm font-medium mb-2">Business Impact</label>
          <textarea
            value={formData.businessImpact}
            onChange={(e) => setFormData(prev => ({ ...prev, businessImpact: e.target.value }))}
            placeholder="Why is this important? What's the business outcome?"
            rows={3}
            className="w-full px-4 py-2 border rounded-lg text-sm"
          />
        </div>
      </div>

      {/* Approach Section */}
      <div className="border-t pt-4">
        <h3 className="font-semibold mb-4">🎯 PREFERRED APPROACH</h3>
        
        <div className="space-y-3">
          {[
            { key: 'needsCoordinator', label: 'Need a manager to coordinate' },
            { key: 'needsSpecialist', label: 'Need multiple specialists working in parallel' },
            { key: 'parallelWork', label: 'Need final approval before delivery' },
            { key: 'needsApproval', label: 'Need to break this into smaller subtasks' }
          ].map(option => (
            <label key={option.key} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="checkbox"
                checked={formData.preferredApproach[option.key]}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  preferredApproach: {
                    ...prev.preferredApproach,
                    [option.key]: e.target.checked
                  }
                }))}
                className="mr-3"
              />
              <span className="text-sm">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-end pt-4 border-t">
        <button className="px-6 py-2 border rounded-lg hover:bg-gray-50">Back</button>
        <button
          onClick={() => onSubmit(formData)}
          disabled={!isValid || isLoading}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Loading...' : 'Next'}
        </button>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Implement form state
- [ ] Add urgency warnings
- [ ] Style radio/checkbox groups
- [ ] Add validation
- [ ] Test all interactions

#### 1.8 Step 3: Review & Launch
**File:** `frontend/src/components/wizard/Step3Review.tsx`

```typescript
import React from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';

interface Step3Props {
  recommendations: any;
  onConfirm: () => void;
  isLoading: boolean;
}

export const Step3Review: React.FC<Step3Props> = ({ recommendations, onConfirm, isLoading }) => {
  return (
    <div className="space-y-6 p-6 bg-white rounded-lg">
      <div>
        <h2 className="text-2xl font-semibold mb-2">✅ Review & Launch</h2>
        <p className="text-gray-600 text-sm">Here's our recommended approach</p>
      </div>

      {/* Task Summary */}
      <div className="border rounded-lg p-4 bg-blue-50">
        <h3 className="font-semibold mb-3">Task Summary</h3>
        <div className="space-y-2 text-sm">
          <div><strong>Title:</strong> {recommendations.title}</div>
          <div><strong>Priority:</strong> {recommendations.priority}</div>
          <div><strong>Due:</strong> {recommendations.due_date}</div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold mb-3">🤖 Recommended Approach</h3>
        
        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{recommendations.execution_approach === 'manager_coordinates' ? '👨‍💼' : '⚙️'}</span>
              <div>
                <div className="font-medium">{recommendations.execution_approach}</div>
                <div className="text-sm text-gray-600 flex items-center gap-1">
                  <CheckCircle size={14} />
                  {(recommendations.confidence * 100).toFixed(0)}% confidence
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-700">{recommendations.reasoning}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="bg-gray-50 p-3 rounded">
              <div className="font-medium mb-2">📊 Estimated Steps</div>
              <div className="text-2xl font-bold text-blue-600">{recommendations.estimated_steps}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="font-medium mb-2">⏱️ Estimated Duration</div>
              <div className="text-lg">{recommendations.duration}</div>
            </div>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
            <div className="font-medium mb-2">⚠️ Potential Risks</div>
            <ul className="list-disc list-inside space-y-1">
              {recommendations.risk_factors.map((risk: string, idx: number) => (
                <li key={idx}>{risk}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* What Happens Next */}
      <div className="border rounded-lg p-4 bg-green-50">
        <h3 className="font-semibold mb-3">🚀 What Happens Next</h3>
        <ol className="space-y-2 text-sm">
          <li><strong>1.</strong> Task is created and ready</li>
          <li><strong>2.</strong> Manager creates an execution plan</li>
          <li><strong>3.</strong> You review and approve the plan</li>
          <li><strong>4.</strong> Team executes and you get updates</li>
          <li><strong>5.</strong> Results delivered and ready to use</li>
        </ol>
      </div>

      {/* Navigation */}
      <div className="flex gap-3 justify-end pt-4 border-t">
        <button className="px-6 py-2 border rounded-lg hover:bg-gray-50">Back</button>
        <button
          onClick={onConfirm}
          disabled={isLoading}
          className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? 'Creating...' : '✓ Create & Start Workflow'}
        </button>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Display recommendations
- [ ] Show confidence scores
- [ ] List risk factors
- [ ] Explain next steps
- [ ] Style information hierarchy
- [ ] Add success animation

---

## 🗓️ WEEK 2: REAL-TIME PROGRESS DASHBOARD & LIVE UPDATES

### Sprint Goal
Implement live progress tracking with WebSocket updates, timeline visualization, and delegation chain display.

### Backend Tasks (1-2 days)

#### 2.1 WebSocket Endpoint for Task Updates
**File:** `backend/app/routes/ws.py`

```python
from fastapi import WebSocket, APIRouter, Depends
from app.core.centrifugo import centrifugo
from app.db.supabase import SupabaseClient

router = APIRouter()

@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_updates(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task updates.
    Sends status changes, progress updates, and events.
    """
    await websocket.accept()
    
    try:
        # Subscribe to task-specific channel
        channel = f"task:{task_id}"
        
        # Send initial state
        initial_data = await get_task_state(task_id)
        await websocket.send_json({
            "type": "initial_state",
            "data": initial_data
        })
        
        # Stream updates from Centrifugo
        async for message in centrifugo.listen(channel):
            await websocket.send_json(message)
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

async def get_task_state(task_id: str) -> dict:
    """
    Get complete current state of a task.
    """
    db = SupabaseClient()
    
    task = db.table('tasks').select('*').eq('id', task_id).single().execute()
    events = db.table('task_events').select('*').eq('task_id', task_id).order('created_at', desc=True).execute()
    
    return {
        'task_id': task_id,
        'current_phase': task.data['current_phase'],
        'current_agent': task.data['current_agent_type'],
        'events': events.data,
        'plan': task.data.get('execution_plan'),
        'result': task.data.get('result_details')
    }
```

**Checklist:**
- [ ] Implement WebSocket handler
- [ ] Add authentication
- [ ] Add error handling
- [ ] Test with multiple clients
- [ ] Monitor connection health

#### 2.2 Event Publishing Updates
**File:** `backend/app/services/task_events.py`

```python
from app.core.centrifugo import centrifugo
from app.db.supabase import SupabaseClient
import json
from datetime import datetime

db = SupabaseClient()

async def publish_task_event(task_id: str, customer_id: str, event_type: str, event_data: dict, agent_type: str = None):
    """
    Publish a task event to both database and WebSocket channel.
    """
    
    # Save to database
    event_record = {
        'task_id': task_id,
        'customer_id': customer_id,
        'event_type': event_type,
        'event_data': event_data,
        'agent_type': agent_type,
        'triggered_by': 'system',
        'created_at': datetime.utcnow().isoformat()
    }
    
    db.table('task_events').insert(event_record).execute()
    
    # Publish to WebSocket subscribers
    await centrifugo.publish(
        channel=f"task:{task_id}",
        data={
            'type': event_type,
            'data': event_data,
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent_type
        }
    )
    
    # Also publish to customer channel for dashboard updates
    await centrifugo.publish(
        channel=f"customer:{customer_id}:tasks",
        data={
            'type': 'task_update',
            'task_id': task_id,
            'event_type': event_type,
            'updated_at': datetime.utcnow().isoformat()
        }
    )

async def publish_status_change(task_id: str, customer_id: str, from_status: str, to_status: str, agent_type: str = None):
    """
    Publish status change event.
    """
    await publish_task_event(
        task_id=task_id,
        customer_id=customer_id,
        event_type='status_change',
        event_data={
            'from': from_status,
            'to': to_status,
            'agent': agent_type
        },
        agent_type=agent_type
    )

async def publish_agent_decision(task_id: str, customer_id: str, agent_type: str, decision: str, confidence: float, reason: str):
    """
    Publish agent decision event.
    """
    await publish_task_event(
        task_id=task_id,
        customer_id=customer_id,
        event_type='agent_decision',
        event_data={
            'decision': decision,
            'confidence': confidence,
            'reason': reason
        },
        agent_type=agent_type
    )

async def publish_plan_created(task_id: str, customer_id: str, plan: dict, confidence: float):
    """
    Publish plan creation event.
    """
    await publish_task_event(
        task_id=task_id,
        customer_id=customer_id,
        event_type='plan_created',
        event_data={
            'plan_id': plan.get('id'),
            'steps_count': len(plan.get('steps', [])),
            'confidence': confidence,
            'preview': plan.get('initial_thought', '')
        }
    )
```

**Checklist:**
- [ ] Update OrchestratorWorkflow to call these functions
- [ ] Update IntelligentDelegationWorkflow to publish events
- [ ] Add logging
- [ ] Test event delivery

### Frontend Tasks (2-3 days)

#### 2.3 Live Progress Dashboard Component
**File:** `frontend/src/components/TaskProgressDashboard.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { useTaskStore } from '../stores/taskStore';
import { ExecutionTimeline } from './progress/ExecutionTimeline';
import { CurrentAgentWidget } from './progress/CurrentAgentWidget';
import { DelegationChain } from './progress/DelegationChain';
import { NotificationFeed } from './progress/NotificationFeed';

interface TaskProgressDashboardProps {
  taskId: string;
}

export const TaskProgressDashboard: React.FC<TaskProgressDashboardProps> = ({ taskId }) => {
  const store = useTaskStore();
  const [wsConnected, setWsConnected] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(`/ws/tasks/${taskId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
      store.subscribeToUpdates(ws);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      store.handleWebSocketMessage(message);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsConnected(false);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
    };
    
    return () => ws.close();
  }, [taskId]);

  if (!store.task) return <div>Loading...</div>;

  return (
    <div className="space-y-6 p-6">
      {/* Header with Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{store.task.title}</h1>
          <div className="flex items-center gap-2 mt-2">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              store.currentPhase === 'completed' ? 'bg-green-100 text-green-800' :
              store.currentPhase === 'planning' ? 'bg-blue-100 text-blue-800' :
              store.currentPhase === 'delegating' ? 'bg-purple-100 text-purple-800' :
              store.currentPhase === 'executing' ? 'bg-orange-100 text-orange-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              {store.currentPhase.toUpperCase()}
            </span>
            <span className={`text-sm ${
              wsConnected ? 'text-green-600' : 'text-gray-600'
            }`}>
              {wsConnected ? '🟢 Live' : '⚫ Offline'}
            </span>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg border ${
              autoRefresh ? 'bg-blue-50 border-blue-300' : 'border-gray-300'
            }`}
          >
            {autoRefresh ? '✓ Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* Column 1: Timeline */}
        <div className="col-span-1">
          <ExecutionTimeline events={store.events} />
        </div>
        
        {/* Column 2: Current Agent */}
        <div className="col-span-1">
          <CurrentAgentWidget agent={store.currentAgent} />
        </div>
        
        {/* Column 3: Delegation Chain */}
        <div className="col-span-1">
          <DelegationChain chain={store.delegationChain} />
        </div>
      </div>

      {/* Notifications Feed */}
      <NotificationFeed notifications={store.notifications} />
    </div>
  );
};
```

**Checklist:**
- [ ] Implement WebSocket connection
- [ ] Handle connection state
- [ ] Display status badge
- [ ] Show live indicator
- [ ] Implement auto-refresh toggle

#### 2.4 Execution Timeline Component
**File:** `frontend/src/components/progress/ExecutionTimeline.tsx`

```typescript
import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface Event {
  type: string;
  timestamp: string;
  data: any;
  agent?: string;
}

interface ExecutionTimelineProps {
  events: Event[];
}

export const ExecutionTimeline: React.FC<ExecutionTimelineProps> = ({ events }) => {
  const timelineItems = [
    { phase: 'created', label: 'Task Created' },
    { phase: 'planning', label: 'Planning Phase' },
    { phase: 'approved', label: 'Plan Approved' },
    { phase: 'delegating', label: 'Delegating' },
    { phase: 'executing', label: 'Executing' },
    { phase: 'completed', label: 'Completed' }
  ];

  const getPhaseStatus = (phase: string) => {
    const event = events.find(e => e.data?.to === phase);
    if (event) {
      return 'completed';
    }
    // Check if current phase
    return 'pending';
  };

  return (
    <div className="border rounded-lg p-4 bg-white">
      <h3 className="font-semibold mb-4">📋 Timeline</h3>
      
      <div className="space-y-3">
        {timelineItems.map((item, idx) => {
          const status = getPhaseStatus(item.phase);
          const event = events.find(e => e.data?.to === item.phase);
          const timestamp = event?.timestamp ? new Date(event.timestamp) : null;
          
          return (
            <motion.div
              key={item.phase}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="flex items-start gap-3"
            >
              <div className="flex-shrink-0 mt-1">
                {status === 'completed' ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <Clock className="text-gray-300" size={20} />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{item.label}</div>
                {timestamp && (
                  <div className="text-xs text-gray-500">
                    {timestamp.toLocaleTimeString()} ({timestamp.toLocaleDateString()})
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Implement timeline display
- [ ] Show completion status
- [ ] Display timestamps
- [ ] Add animations
- [ ] Handle pending states

#### 2.5 Current Agent Widget
**File:** `frontend/src/components/progress/CurrentAgentWidget.tsx`

```typescript
import React from 'react';
import { Zap, Clock, Brain } from 'lucide-react';

interface Agent {
  type: string;
  name: string;
  status: string;
  elapsedTime: number;
  estimatedRemaining: number;
  currentTask: string;
  progressPercent: number;
}

interface CurrentAgentWidgetProps {
  agent: Agent | null;
}

export const CurrentAgentWidget: React.FC<CurrentAgentWidgetProps> = ({ agent }) => {
  if (!agent) {
    return (
      <div className="border rounded-lg p-4 bg-white">
        <h3 className="font-semibold mb-4">⏳ Waiting...</h3>
        <p className="text-sm text-gray-600">No agent active yet</p>
      </div>
    );
  }

  const statusColor = agent.status === 'active' ? 'bg-green-100' : 'bg-yellow-100';
  const statusText = agent.status === 'active' ? '🟢 Active & Responding' : '⏸️ Waiting';

  return (
    <div className="border rounded-lg p-4 bg-white">
      <h3 className="font-semibold mb-3">👤 Current Agent</h3>
      
      <div className={`p-3 rounded ${statusColor} mb-3`}>
        <div className="font-medium text-sm">{statusText}</div>
      </div>
      
      <div className="space-y-3 text-sm">
        <div>
          <div className="text-gray-600">Agent</div>
          <div className="font-medium">{agent.name} ({agent.type})</div>
        </div>
        
        <div>
          <div className="text-gray-600">Current Task</div>
          <div className="font-medium">{agent.currentTask}</div>
        </div>
        
        <div>
          <div className="text-gray-600 flex items-center gap-2">
            <Clock size={14} /> Time Spent
          </div>
          <div className="font-medium">{Math.round(agent.elapsedTime / 60)} seconds</div>
        </div>
        
        <div>
          <div className="text-gray-600">Progress</div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${agent.progressPercent}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">{agent.progressPercent}%</div>
        </div>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Display agent info
- [ ] Show status indicator
- [ ] Display progress bar
- [ ] Show elapsed time
- [ ] Update in real-time

#### 2.6 Delegation Chain Visualization
**File:** `frontend/src/components/progress/DelegationChain.tsx`

```typescript
import React from 'react';
import { ArrowDown } from 'lucide-react';

interface DelegationStep {
  agent: string;
  decision: string;
  confidence: number;
  status: 'completed' | 'active' | 'pending';
  timestamp?: string;
}

interface DelegationChainProps {
  chain: DelegationStep[];
}

export const DelegationChain: React.FC<DelegationChainProps> = ({ chain }) => {
  return (
    <div className="border rounded-lg p-4 bg-white">
      <h3 className="font-semibold mb-4">🔗 Delegation Chain</h3>
      
      <div className="space-y-2">
        {chain.map((step, idx) => (
          <React.Fragment key={idx}>
            {idx > 0 && (
              <div className="flex justify-center py-1">
                <ArrowDown className="text-gray-300" size={20} />
              </div>
            )}
            
            <div className={`p-3 rounded border text-sm ${
              step.status === 'completed' ? 'bg-green-50 border-green-200' :
              step.status === 'active' ? 'bg-blue-50 border-blue-200' :
              'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="font-medium">{step.agent}</div>
                <div className={`text-xs px-2 py-1 rounded-full ${
                  step.status === 'completed' ? 'bg-green-200 text-green-800' :
                  step.status === 'active' ? 'bg-blue-200 text-blue-800' :
                  'bg-gray-200 text-gray-800'
                }`}>
                  {step.status === 'completed' ? '✓ Done' :
                   step.status === 'active' ? '🔄 Working' :
                   '⏳ Pending'}
                </div>
              </div>
              
              <div className="mt-2">
                <div className="text-xs text-gray-600">Decision: {step.decision}</div>
                <div className="text-xs text-gray-600">Confidence: {(step.confidence * 100).toFixed(0)}%</div>
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>
      
      <div className="mt-3 text-xs text-gray-600 bg-blue-50 p-2 rounded">
        Depth: {chain.length}/5 (Still within safe limits)
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Display delegation steps
- [ ] Show decision status
- [ ] Display confidence scores
- [ ] Add connecting arrows
- [ ] Show depth limit warning

#### 2.7 Notification Feed Component
**File:** `frontend/src/components/progress/NotificationFeed.tsx`

```typescript
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, Clock, Info } from 'lucide-react';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationFeedProps {
  notifications: Notification[];
}

export const NotificationFeed: React.FC<NotificationFeedProps> = ({ notifications }) => {
  const [expanded, setExpanded] = React.useState(false);
  const unreadCount = notifications.filter(n => !n.read).length;

  const getIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="text-green-500" size={16} />;
      case 'warning': return <AlertCircle className="text-yellow-500" size={16} />;
      case 'error': return <AlertCircle className="text-red-500" size={16} />;
      default: return <Info className="text-blue-500" size={16} />;
    }
  };

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <h3 className="font-semibold">📢 Notifications {unreadCount > 0 && `(${unreadCount})`}</h3>
        <span className="text-sm text-gray-500">{expanded ? '▼' : '▶'}</span>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 space-y-2 max-h-96 overflow-y-auto"
          >
            {notifications.slice(0, 10).map((notif, idx) => (
              <motion.div
                key={notif.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`p-2 rounded text-xs border-l-4 ${
                  notif.type === 'success' ? 'bg-green-50 border-green-500' :
                  notif.type === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                  notif.type === 'error' ? 'bg-red-50 border-red-500' :
                  'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-start gap-2">
                  {getIcon(notif.type)}
                  <div className="flex-1">
                    <div className="font-medium">{notif.message}</div>
                    <div className="text-gray-500 text-xs mt-1">
                      {notif.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
```

**Checklist:**
- [ ] Display notifications
- [ ] Show unread count
- [ ] Implement expand/collapse
- [ ] Add icons by type
- [ ] Show timestamps
- [ ] Animate entries

---

## 🗓️ WEEK 3: EXECUTION PLAN REVIEW & RESULTS DELIVERY

### Sprint Goal
Implement execution plan approval workflow and structured results delivery interface.

### Backend Tasks (1 day)

#### 3.1 Plan Approval Endpoint
**File:** `backend/app/routes/plans.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.db.supabase import SupabaseClient
from app.services.task_events import publish_task_event

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/{plan_id}/approve")
async def approve_plan(
    plan_id: str,
    user = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    User approves the execution plan for a task.
    """
    plan = db.table('tasks').select('*').eq('id', plan_id).single().execute()
    
    if plan.data['created_by'] != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Update task
    db.table('tasks').update({
        'plan_approved_at': datetime.utcnow().isoformat(),
        'plan_approved_by': user.id,
        'current_phase': 'delegating'
    }).eq('id', plan_id).execute()
    
    # Publish event
    await publish_task_event(
        task_id=plan_id,
        customer_id=user.customer_id,
        event_type='plan_approved',
        event_data={'approved_by': user.id}
    )
    
    return {'status': 'approved', 'message': 'Plan approved. Starting delegation...'}

@router.post("/{plan_id}/reject")
async def reject_plan(
    plan_id: str,
    feedback: str = None,
    user = Depends(get_current_user),
    db: SupabaseClient = Depends(get_db)
):
    """
    User rejects the plan and asks for changes.
    """
    # Publish event
    await publish_task_event(
        task_id=plan_id,
        customer_id=user.customer_id,
        event_type='plan_rejected',
        event_data={'feedback': feedback}
    )
    
    return {'status': 'rejected', 'message': 'Plan rejected. Manager will create a new plan.'}
```

**Checklist:**
- [ ] Implement approval endpoint
- [ ] Add validation
- [ ] Publish events
- [ ] Update task status
- [ ] Write tests

#### 3.2 Results Submission Endpoint
**File:** `backend/app/routes/results.py`

```python
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    result_data: dict,
    quality_score: int,
    db: SupabaseClient = Depends(get_db)
):
    """
    Mark task as completed with results.
    """
    task = db.table('tasks').select('*').eq('id', task_id).single().execute()
    
    # Update task with results
    db.table('tasks').update({
        'current_phase': 'completed',
        'result_details': result_data,
        'quality_score': min(100, max(0, quality_score)),
        'actual_duration_minutes': calculate_duration(task.data['created_at'])
    }).eq('id', task_id).execute()
    
    # Publish completion event
    await publish_task_event(
        task_id=task_id,
        customer_id=task.data['customer_id'],
        event_type='task_completed',
        event_data={
            'quality_score': quality_score,
            'result_summary': result_data.get('summary', '')
        }
    )
    
    return {'status': 'completed', 'quality_score': quality_score}
```

**Checklist:**
- [ ] Implement completion endpoint
- [ ] Calculate quality score
- [ ] Store results
- [ ] Calculate actual duration
- [ ] Publish events

### Frontend Tasks (2 days)

#### 3.3 Plan Approval View
**File:** `frontend/src/components/PlanApprovalView.tsx`

```typescript
import React, { useState } from 'react';
import { ChevronDown, AlertCircle } from 'lucide-react';

interface ExecutionPlan {
  id: string;
  initial_thought: string;
  steps: Array<{
    description: string;
    output_type: string;
    estimated_time: string;
  }>;
  timeline: string;
  resources_needed: string[];
}

interface PlanApprovalViewProps {
  plan: ExecutionPlan;
  agentRecommendation: {
    action: string;
    reason: string;
    confidence: number;
  };
  onApprove: () => void;
  onReject: () => void;
  isLoading: boolean;
}

export const PlanApprovalView: React.FC<PlanApprovalViewProps> = ({
  plan,
  agentRecommendation,
  onApprove,
  onReject,
  isLoading
}) => {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);
  const [feedback, setFeedback] = useState('');

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h2 className="text-xl font-semibold mb-2">📋 Execution Plan Review</h2>
        <p className="text-sm text-gray-700">Review the plan created by the agent. Approve to proceed or request changes.</p>
      </div>

      {/* Agent's Analysis */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold mb-3">🤖 Agent Analysis</h3>
        <div className="bg-blue-50 p-3 rounded border border-blue-200 text-sm">
          <p className="font-medium mb-2">{plan.initial_thought}</p>
        </div>
      </div>

      {/* Plan Steps */}
      <div className="border rounded-lg p-4">
        <h3 className="font-semibold mb-4">📋 Execution Steps ({plan.steps.length})</h3>
        <div className="space-y-2">
          {plan.steps.map((step, idx) => (
            <div
              key={idx}
              className="border rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setExpandedStep(expandedStep === idx ? null : idx)}
                className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
              >
                <div className="flex items-center gap-3 text-left">
                  <span className="font-bold text-blue-600">{idx + 1}</span>
                  <div>
                    <div className="font-medium">{step.description}</div>
                    <div className="text-xs text-gray-600">Output: {step.output_type}</div>
                  </div>
                </div>
                <ChevronDown
                  size={20}
                  className={`transform transition ${
                    expandedStep === idx ? 'rotate-180' : ''
                  }`}
                />
              </button>
              
              {expandedStep === idx && (
                <div className="p-4 bg-white border-t">
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Description:</strong>
                      <p className="text-gray-700">{step.description}</p>
                    </div>
                    <div>
                      <strong>Output Type:</strong>
                      <p className="text-gray-700">{step.output_type}</p>
                    </div>
                    <div>
                      <strong>Estimated Time:</strong>
                      <p className="text-gray-700">{step.estimated_time}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Timeline & Resources */}
      <div className="grid grid-cols-2 gap-4">
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold mb-2">⏱️ Timeline</h4>
          <p className="text-sm text-gray-700">{plan.timeline}</p>
        </div>
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold mb-2">📦 Resources Needed</h4>
          <ul className="text-sm space-y-1">
            {plan.resources_needed.map((resource, idx) => (
              <li key={idx}>• {resource}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Agent Recommendation */}
      <div className="border rounded-lg p-4 bg-green-50 border-green-200">
        <h3 className="font-semibold mb-3">🎯 Agent Recommendation</h3>
        <div className="space-y-2 text-sm">
          <div>
            <strong>Decision:</strong>
            <p className="text-gray-700 capitalize">{agentRecommendation.action}</p>
          </div>
          <div>
            <strong>Reasoning:</strong>
            <p className="text-gray-700">{agentRecommendation.reason}</p>
          </div>
          <div>
            <strong>Confidence:</strong>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${agentRecommendation.confidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium">
                {(agentRecommendation.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback Section */}
      <div className="border rounded-lg p-4">
        <h4 className="font-semibold mb-3">📝 Request Changes (optional)</h4>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="If you'd like changes, describe them here. Leave empty to proceed as-is."
          className="w-full px-4 py-2 border rounded-lg text-sm"
          rows={3}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <button
          onClick={onReject}
          disabled={isLoading}
          className="px-6 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          Request Changes
        </button>
        <button
          onClick={onApprove}
          disabled={isLoading}
          className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading ? 'Approving...' : '✓ Approve & Proceed'}
        </button>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Display plan steps
- [ ] Implement expand/collapse
- [ ] Show timeline & resources
- [ ] Display agent recommendation
- [ ] Add feedback textarea
- [ ] Implement approve/reject logic

#### 3.4 Results View Component
**File:** `frontend/src/components/ResultsView.tsx`

```typescript
import React, { useState } from 'react';
import { Download, Share2, Copy } from 'lucide-react';
import { ResultsTabs } from './results/ResultsTabs';
import { FeedbackForm } from './results/FeedbackForm';
import { AgentPerformance } from './results/AgentPerformance';

interface ResultsViewProps {
  taskId: string;
  task: any;
  result: any;
  qualityScore: number;
  executionHistory: any[];
  agentPerformance: any[];
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  taskId,
  task,
  result,
  qualityScore,
  executionHistory,
  agentPerformance
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleExportPDF = () => {
    // Export result as PDF
    console.log('Exporting as PDF...');
  };

  const handleShare = () => {
    // Share result
    console.log('Sharing...');
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">✅ Task Completed</h1>
          <p className="text-gray-600 mt-1">{task.title}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleShare}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Share2 size={18} /> Share
          </button>
          <button
            onClick={handleExportPDF}
            className="px-4 py-2 border rounded-lg hover:bg-gray-50 flex items-center gap-2"
          >
            <Download size={18} /> Export
          </button>
        </div>
      </div>

      {/* Quality Score Card */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-6">
        <h3 className="text-sm font-medium opacity-90">Quality Score</h3>
        <div className="text-5xl font-bold mt-2">{qualityScore}</div>
        <div className="text-sm mt-2 opacity-90">Excellent delivery quality</div>
      </div>

      {/* Tabs */}
      <ResultsTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">📊 Delivery Summary</h2>
            <div className="prose prose-sm max-w-none">
              {result.summary}
            </div>
          </div>
        )}
        
        {activeTab === 'breakdown' && (
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">📋 Detailed Breakdown</h2>
            {/* Render structured results */}
            {result.breakdown && (
              <div className="space-y-6">
                {Object.entries(result.breakdown).map(([key, value]) => (
                  <div key={key}>
                    <h4 className="font-semibold mb-2 capitalize">{key.replace(/_/g, ' ')}</h4>
                    <div className="bg-gray-50 p-4 rounded">
                      {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'history' && (
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">🕐 Execution History</h2>
            <div className="space-y-2">
              {executionHistory.map((event, idx) => (
                <div key={idx} className="flex items-start gap-3 pb-3 border-b last:border-b-0">
                  <span className="text-xs text-gray-500 min-w-max">✓</span>
                  <div>
                    <div className="font-medium text-sm">{event.event_type}</div>
                    <div className="text-xs text-gray-600">{event.created_at}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {activeTab === 'agents' && (
          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-4">🤖 Agent Performance</h2>
            <AgentPerformance agents={agentPerformance} />
          </div>
        )}
      </div>

      {/* Feedback Section */}
      {!feedbackSubmitted && (
        <div className="border rounded-lg p-6 bg-white">
          <h2 className="text-xl font-semibold mb-4">🎯 Your Feedback</h2>
          <FeedbackForm
            onSubmit={() => setFeedbackSubmitted(true)}
            taskId={taskId}
          />
        </div>
      )}

      {/* Next Actions */}
      <div className="border rounded-lg p-6 bg-blue-50">
        <h2 className="text-xl font-semibold mb-4">🚀 Next Steps</h2>
        <div className="space-y-2 text-sm">
          <button className="block w-full text-left px-4 py-2 bg-white border rounded hover:bg-gray-50">
            📅 Schedule Posts (if social media)
          </button>
          <button className="block w-full text-left px-4 py-2 bg-white border rounded hover:bg-gray-50">
            👥 Share with Team
          </button>
          <button className="block w-full text-left px-4 py-2 bg-white border rounded hover:bg-gray-50">
            📋 Create Related Task
          </button>
        </div>
      </div>
    </div>
  );
};
```

**Checklist:**
- [ ] Display quality score prominently
- [ ] Implement tabbed interface
- [ ] Show execution history
- [ ] Display agent performance
- [ ] Add feedback form
- [ ] Show next actions
- [ ] Implement export/share

---

## 🗓️ WEEK 4: ERROR HANDLING, POLISH, & DEPLOYMENT

### Sprint Goal
Implement comprehensive error handling, mobile responsiveness, accessibility, and prepare for production deployment.

### Tasks (2-3 days)

#### 4.1 Error State Components
**File:** `frontend/src/components/ErrorStates.tsx`

```typescript
// Comprehensive error handling for all scenarios
```

#### 4.2 Mobile Responsiveness
- [ ] Test all views on mobile
- [ ] Adjust layout for small screens
- [ ] Ensure touch interactions work
- [ ] Test performance on 3G

#### 4.3 Accessibility
- [ ] Add ARIA labels
- [ ] Ensure keyboard navigation
- [ ] Test with screen readers
- [ ] Verify color contrast
- [ ] Add focus indicators

#### 4.4 Performance Optimization
- [ ] Code splitting
- [ ] Lazy loading components
- [ ] Image optimization
- [ ] Bundle analysis
- [ ] Load time testing

#### 4.5 Testing
- [ ] Unit tests for components
- [ ] Integration tests for workflows
- [ ] E2E tests for user flows
- [ ] WebSocket connection tests
- [ ] Real-time update tests

#### 4.6 Documentation
- [ ] Component API docs
- [ ] User guide
- [ ] Developer guide
- [ ] Troubleshooting guide
- [ ] API documentation updates

#### 4.7 Feature Flags & Rollout
```python
# Enable gradual rollout
FEATURE_FLAGS = {
    'new_task_wizard': {
        'enabled': True,
        'rollout_percentage': 10  # Start with 10% of users
    },
    'live_progress_dashboard': {
        'enabled': True,
        'rollout_percentage': 10
    },
    'plan_approval_workflow': {
        'enabled': True,
        'rollout_percentage': 10
    },
    'enhanced_results_view': {
        'enabled': True,
        'rollout_percentage': 10
    }
}
```

**Checklist:**
- [ ] Implement feature flags
- [ ] Set up gradual rollout
- [ ] Monitor analytics
- [ ] Collect user feedback
- [ ] Prepare rollback plan

---

## 📊 SUCCESS METRICS

### Track These KPIs

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Task Creation Completion Rate | 65% | 95% | % tasks created to completion |
| Average Creation Time | 3 min | 8 min | Time from start to workflow launch |
| Plan Approval Rate | N/A | 92% | % plans approved without changes |
| User Satisfaction | N/A | 4.5/5 | Post-task feedback rating |
| Error Recovery Rate | 20% | 90% | % users who retry vs abandon |
| Real-time Update Latency | N/A | <500ms | Time from event to UI update |
| Page Load Time | 2.5s | <1.5s | Time to interactive |
| Mobile Satisfaction | N/A | 4.5/5 | Mobile-specific ratings |

### Monitoring & Alerts

```python
# Track in analytics/monitoring
metrics = {
    'task_creation_funnel': {
        'step1_views': metric(),
        'step1_completions': metric(),
        'step2_views': metric(),
        'step2_completions': metric(),
        'step3_views': metric(),
        'step3_completions': metric(),
    },
    'plan_approval': {
        'plans_created': metric(),
        'plans_approved': metric(),
        'plans_rejected': metric(),
        'plans_changed': metric(),
    },
    'real_time_performance': {
        'websocket_connections': metric(),
        'message_latency_ms': metric(),
        'update_frequency': metric(),
    },
    'errors': {
        'creation_errors': metric(),
        'websocket_disconnects': metric(),
        'api_errors': metric(),
    }
}
```

---

## 🎯 RISK MITIGATION

### Identified Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|----------|
| WebSocket connection instability | Medium | High | Add reconnection logic, fallback to polling |
| Real-time data out of sync | Medium | Medium | Implement optimistic updates + verification |
| Performance degradation with many events | Low | High | Implement event filtering, pagination |
| Accessibility issues | Low | Medium | Early testing with screen readers |
| Mobile UX poor | Medium | Medium | Mobile-first design, early testing |
| Recommendation engine errors | Low | Medium | Add fallback heuristics |
| Database query performance | Low | Medium | Add caching, optimize indexes |
| User adoption low | Medium | High | Good UX, onboarding, feature education |

---

## 📋 DAILY STANDUP TEMPLATE

```
WEEK 1 - Task Creation Wizard
=============================
Day 1 (Monday):
- [ ] Database migrations completed
- [ ] API endpoints implemented
- [ ] Frontend form components started

Day 2 (Tuesday):
- [ ] All form components completed
- [ ] API integration tested
- [ ] Styling 80% complete

Day 3 (Wednesday):
- [ ] All styling complete
- [ ] Form validation working
- [ ] Error states implemented

Day 4 (Thursday):
- [ ] Recommendation engine integrated
- [ ] End-to-end flow tested
- [ ] Performance optimized

Day 5 (Friday):
- [ ] QA testing
- [ ] Bug fixes
- [ ] Documentation completed
```

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment (Friday Before Week 2)
- [ ] All tests passing (>90% coverage)
- [ ] Code reviewed by 2+ team members
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Staging deployment successful
- [ ] E2E tests passing on staging
- [ ] Documentation complete
- [ ] Rollback plan documented

### Deployment Day
- [ ] Database migrations run on production
- [ ] Feature flag disabled by default
- [ ] Deployment completed
- [ ] Smoke tests passing
- [ ] Enable feature flag at 10%
- [ ] Monitor for 30 minutes
- [ ] Gradually increase to 100%
- [ ] Final verification

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Be ready to rollback if needed
- [ ] Update runbooks

---

## 📞 SUPPORT & ESCALATION

### Support Matrix

| Issue | Owner | Escalation | Response Time |
|-------|-------|-----------|---------------|
| Frontend bugs | Frontend Lead | CTO | 30 min |
| Backend API issues | Backend Lead | CTO | 30 min |
| WebSocket problems | DevOps | CTO | 15 min |
| Performance degradation | DevOps | CTO | 15 min |
| Database issues | DBA | VP Eng | 15 min |
| User experience feedback | PM | Frontend Lead | Next standup |

---

## 🎓 TEAM TRAINING

### Required Training Before Execution
1. **Architecture Deep Dive** (30 min)
   - Overview of new components
   - Data flow diagrams
   - WebSocket integration

2. **Frontend Workshop** (2 hours)
   - Zustand state management
   - Framer Motion animations
   - Tailwind styling system
   - Component patterns

3. **Backend Workshop** (2 hours)
   - Temporal workflows
   - Activity patterns
   - Event publishing
   - Database schema

4. **Testing Strategy** (1 hour)
   - Unit test patterns
   - Integration test patterns
   - E2E test patterns
   - Performance testing

---

## 💰 RESOURCE REQUIREMENTS

### Team
- **2 Full-Stack Engineers** (primary development)
- **1 QA Engineer** (testing & validation)
- **1 Product Manager** (requirements & feedback)
- **1 Designer** (UX review)

### Infrastructure
- **Staging Database** (for migrations testing)
- **Staging Environment** (for full testing)
- **Monitoring & Analytics** (for metrics tracking)
- **CDN** (for asset delivery)

### Budget
- Development Time: ~160-200 hours
- QA Time: ~40 hours
- Infrastructure: ~$500-1000
- Tools & Services: ~$200
- **Total: ~$15K-25K** (depending on team cost)

---

## 📚 DELIVERABLES SUMMARY

### By End of Week 1
✅ 3-step task creation wizard  
✅ Database schema enhancements  
✅ API endpoints for task creation  
✅ Recommendation engine integration  

### By End of Week 2
✅ Real-time progress dashboard  
✅ WebSocket integration  
✅ Live timeline visualization  
✅ Delegation chain display  

### By End of Week 3
✅ Execution plan approval workflow  
✅ Structured results delivery  
✅ User feedback collection  
✅ Agent performance display  

### By End of Week 4
✅ Comprehensive error handling  
✅ Mobile responsive design  
✅ Full accessibility support  
✅ Production deployment ready  
✅ Complete documentation  

---

**Next Step:** Schedule kickoff meeting for Monday!  
**Questions?** Reach out to the tech lead.
