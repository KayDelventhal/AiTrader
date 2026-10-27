import type { components } from '../../client/schema'

export type CostEntry = components['schemas']['CostEntryView']
export type CostCategory = CostEntry['category']
export type CostStatus = CostEntry['status']
export type RecurringCost = components['schemas']['RecurringCostView']
export type CostSummary = components['schemas']['CostSummary']
export type PerformanceCostView = components['schemas']['PerformanceCostView']
