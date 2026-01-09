// Modern feature gating (2025) - Use this for new implementations
export { FeatureGateModal } from './FeatureGateModal';
export type { FeatureContext } from './FeatureGateModal';

// Legacy components (deprecated - use FeatureGateModal instead)
export { FeatureGate, SimpleFeatureGate, useConditionalFeature } from './FeatureGate';
export { SubscriptionGate } from './SubscriptionGate';
export { PlanGate } from './PlanGate';
export { UpgradePrompt } from './UpgradePrompt';