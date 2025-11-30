# Detailed Fix Plan for Agent System Issues

## Executive Summary
This plan addresses 6 critical issues in the pension advisor agent system:
1. Duplicate governance logging
2. Missing classification cost in total
3. Inconsistent phase numbering in comments
4. Disabled MLflow tracing
5. Incomplete cost breakdown
6. Missing classification cost in governance logs

---

## Fix #1: Remove Duplicate Governance Logging ✅

**Issue:** Every query is logged to governance table twice (lines 352-382 and 566-583)

**Root Cause:**
- After `process_query()` returns, there's an immediate logging attempt
- Then Phase 8 does the same logging again

**Files to Modify:**
- `src/agent_processor.py`

**Changes:**
1. DELETE lines 352-382 (first governance logging block after process_query)
2. KEEP lines 566-583 (Phase 8 official logging)
3. KEEP the debug log at line 363 ("About to log to governance table") for tracking

**Testing:**
- Run a query and check governance table
- Should have exactly ONE entry per query
- Verify session_id is unique per query

**Risk:** Low - Simple deletion, Phase 8 logging remains

---

## Fix #2: Add Classification Cost to Total ✅

**Issue:** Classification cost from 3-stage cascade is not included in total_cost

**Root Cause:**
- `result_dict['classification']` contains `cost_usd` field
- But line 517 only sums: `total_cost = total_synthesis_cost + total_validation_cost`

**Files to Modify:**
- `src/agent_processor.py`

**Changes:**
1. After line 515, extract classification cost:
   ```python
   # Extract classification cost
   classification_cost = result_dict.get('classification', {}).get('cost_usd', 0.0)
   ```

2. Update line 517 to include classification:
   ```python
   total_cost = classification_cost + total_synthesis_cost + total_validation_cost
   ```

3. Add log message after line 517:
   ```python
   logger.info(f"💰 Classification cost: ${classification_cost:.6f}")
   ```

**Testing:**
- Run query and check console output
- Should see: "Classification cost: $X.XXXXXX"
- Total cost should be higher than before
- For regex classification, cost should be $0
- For LLM classification, cost should be ~$0.001

**Risk:** Low - Additive change, doesn't break existing functionality

---

## Fix #3: Fix Phase Number Comments ✅

**Issue:** Comments in react_loop.py say "Phase 1, 2, 3, 4" but actual phase keys are "phase_3, phase_4, phase_5, phase_6"

**Root Cause:**
- react_loop.py thinks it's running phases 1-4 (relative to itself)
- But agent_processor.py already ran phases 1-2
- Actual system phases are 1-8 globally

**Files to Modify:**
- `src/react_loop.py`

**Changes:**
1. Line 362: Change comment from "Phase 1: REASON" to "Phase 3: CLASSIFICATION"
2. Line 403: Change comment from "Phase 2: REASON" to "Phase 4: TOOL PLANNING"
3. Line 418: Change comment from "Phase 3: ACT" to "Phase 5: TOOL EXECUTION"
4. Line 432: Change comment from "Phase 4: ITERATE" to "Phase 6: SYNTHESIS + VALIDATION"

**Testing:**
- Read through react_loop.py
- Verify comments match phase keys
- Check console logs show correct phase numbers

**Risk:** None - Comment-only changes

---

## Fix #4: Re-enable MLflow Tracing ✅

**Issue:** `@mlflow.trace` decorator is commented out on line 225

**Root Cause:**
- Was disabled for debugging
- Never re-enabled

**Files to Modify:**
- `src/agent_processor.py`

**Changes:**
1. Line 225: Uncomment the decorator:
   ```python
   # FROM:
   # @mlflow.trace(name="pension_advisor_query", span_type="AGENT")  # TEMPORARILY DISABLED FOR DEBUGGING

   # TO:
   @mlflow.trace(name="pension_advisor_query", span_type="AGENT")
   ```

2. Update the debug log on line 252 to confirm tracing is enabled:
   ```python
   logger.info("🔥 DEBUG: agent_query() started WITH @mlflow.trace enabled")
   ```

**Testing:**
- Run query
- Check MLflow UI for traces
- Should see detailed span breakdown
- Verify no "run already active" errors

**Risk:** Medium - Could cause MLflow conflicts, but safety code exists in observability.py

**Rollback Plan:** If errors occur, re-comment the decorator

---

## Fix #5: Add Classification Cost to Cost Breakdown ✅

**Issue:** `cost_breakdown` dict doesn't include classification breakdown

**Root Cause:**
- Only synthesis and validation are added to cost_breakdown
- Classification is logged to observability but not to cost_breakdown

**Files to Modify:**
- `src/agent_processor.py`

**Changes:**
1. After line 493 (synthesis breakdown), add classification breakdown:
   ```python
   # Extract classification info
   classification_info = result_dict.get('classification', {})
   classification_cost = classification_info.get('cost_usd', 0.0)
   classification_method = classification_info.get('method', 'unknown')

   cost_breakdown['classification'] = {
       'method': classification_method,
       'cost': classification_cost,
       'latency_ms': classification_info.get('latency_ms', 0.0),
       'confidence': classification_info.get('confidence', 0.0)
   }

   logger.info(f"💰 Classification cost: ${classification_cost:.6f} ({classification_method})")
   ```

2. Update line 519 to include all three costs:
   ```python
   cost_breakdown['total'] = {
       'classification_cost': classification_cost,  # NEW
       'synthesis_cost': total_synthesis_cost,
       'validation_cost': total_validation_cost,
       'total_cost': total_cost,  # Already includes classification from Fix #2
       'classification_tokens': 0,  # Classification doesn't use tokens (regex/embedding)
       'synthesis_tokens': total_synthesis_input_tokens + total_synthesis_output_tokens,
       'validation_tokens': total_validation_input_tokens + total_validation_output_tokens,
       'total_tokens': (total_synthesis_input_tokens + total_synthesis_output_tokens +
                       total_validation_input_tokens + total_validation_output_tokens)
   }
   ```

3. Update summary log at line 536 to show classification:
   ```python
   logger.info(f"💰 TOTAL COST: ${total_cost:.6f}")
   logger.info(f"   ├─ Classification: ${classification_cost:.6f} ({classification_method})")
   logger.info(f"   ├─ Synthesis (Opus 4.1):  ${total_synthesis_cost:.6f}")
   logger.info(f"   └─ Validation (Sonnet 4): ${total_validation_cost:.6f}")
   ```

**Testing:**
- Run query
- Check console output for classification cost line
- Check MLflow artifacts for cost_breakdown.json
- Verify all three costs are present

**Risk:** Low - Additive change to existing dict

---

## Fix #6: Update Governance Logging Parameters ✅

**Issue:** Governance logging doesn't receive classification_cost separately (it's lumped into total)

**Root Cause:**
- `log_to_governance_table()` receives `cost=total_cost`
- But doesn't have classification breakdown

**Files to Modify:**
- `src/agent_processor.py`

**Changes:**
1. Line 567-580: The governance logging already receives `classification_method`
2. Update to also include cost breakdown in error_info field (temporary until schema updated):
   ```python
   # Around line 559, after extracting classification_method:
   classification_info = result_dict.get('classification', {})
   classification_method = classification_info.get('method', 'unknown') if classification_info else 'unknown'
   classification_cost_value = classification_info.get('cost_usd', 0.0) if classification_info else 0.0

   # Store in error_info field as JSON (hack until schema updated)
   cost_metadata = {
       'classification_cost': classification_cost_value,
       'classification_method': classification_method,
       'synthesis_cost': total_synthesis_cost,
       'validation_cost': total_validation_cost
   }
   ```

**Note:** The governance table schema doesn't have separate classification_cost column. This is stored in error_info field as a workaround. Future: Add proper columns to schema.

**Testing:**
- Run query
- Check governance table
- Verify error_info contains cost breakdown
- Total cost should match sum of components

**Risk:** Low - Just adding metadata to existing field

---

## Fix Order & Dependencies

```
Fix #1 (Remove duplicate logging)
  ↓
Fix #2 (Add classification cost to total)
  ↓
Fix #5 (Add classification cost to breakdown)
  ↓
Fix #6 (Update governance logging)
  ↓
Fix #3 (Fix comments - independent)
  ↓
Fix #4 (Re-enable tracing - test last)
```

**Why this order?**
1. Fix #1 first: Prevents duplicate records during testing
2. Fix #2: Core calculation must be correct before anything else
3. Fix #5: Breakdown depends on Fix #2
4. Fix #6: Logging depends on Fix #2 and #5
5. Fix #3: Independent, safe anytime
6. Fix #4: Test last because it could cause MLflow errors

---

## Testing Plan

### After Each Fix:
1. Run a test query through the system
2. Check console logs for expected output
3. Verify no Python errors
4. Check governance table for correct data
5. Check MLflow for correct metrics

### Final Integration Test:
1. Run 3 queries with different classification stages:
   - Query 1: "What is my super balance?" (should hit regex - Stage 1)
   - Query 2: "Tell me about my retirement" (should hit embedding - Stage 2)
   - Query 3: "What's the weather?" (should hit LLM - Stage 3)

2. Verify for each query:
   - Exactly ONE governance table entry
   - Total cost = classification + synthesis + validation
   - Cost breakdown shows all three components
   - MLflow traces show detailed spans (after Fix #4)
   - Console logs show all 8 phases with correct numbers

### Success Criteria:
- ✅ No duplicate governance records
- ✅ Classification cost included in total
- ✅ All phase comments match phase keys
- ✅ MLflow tracing active (if Fix #4 applied)
- ✅ Cost breakdown complete
- ✅ No Python errors

---

## Rollback Plan

If any fix causes issues:

1. **Fix #1**: Re-add the deleted logging block (git revert)
2. **Fix #2**: Comment out classification_cost addition
3. **Fix #3**: No rollback needed (comments only)
4. **Fix #4**: Re-comment the @mlflow.trace decorator
5. **Fix #5**: Remove classification from cost_breakdown
6. **Fix #6**: Remove cost_metadata addition

---

## Files Modified Summary

- `src/agent_processor.py` (Fixes #1, #2, #4, #5, #6)
- `src/react_loop.py` (Fix #3)

---

## Estimated Time
- Planning: ✅ Done
- Fix #1: 5 min
- Fix #2: 5 min
- Fix #3: 5 min
- Fix #4: 5 min
- Fix #5: 10 min
- Fix #6: 10 min
- Testing: 20 min
- **Total: ~60 min**

---

## Next Steps
1. Review and approve this plan
2. Create backup branch: `git checkout -b fix/agent-logging-issues`
3. Implement fixes 1-6 in order
4. Test after each fix
5. Final integration test
6. Commit and create PR

---

**Status: PLAN APPROVED - READY TO IMPLEMENT**
