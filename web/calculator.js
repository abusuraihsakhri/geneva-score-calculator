/* Revised Geneva PE pretest probability score (Le Gal et al., 2006). */
(function (root) {
  'use strict';
  const WEIGHTS = Object.freeze({
    previous_dvt_pe: 3,
    surgery_or_fracture_1mo: 2,
    active_malignancy: 2,
    unilateral_leg_pain: 3,
    hemoptysis: 2,
    deep_vein_tenderness_and_unilateral_edema: 4
  });
  const LABELS = Object.freeze({
    previous_dvt_pe: 'Previous DVT or PE',
    surgery_or_fracture_1mo: 'Surgery or fracture within one month',
    active_malignancy: 'Active malignancy',
    unilateral_leg_pain: 'Unilateral lower-limb pain',
    hemoptysis: 'Hemoptysis',
    deep_vein_tenderness_and_unilateral_edema: 'Deep-vein tenderness AND unilateral edema'
  });
  function numberInRange(value, name, min, max) {
    if (value === null || value === undefined || typeof value === 'boolean' ||
        (typeof value === 'string' && !value.trim())) {
      throw new Error(name + ' must be provided');
    }
    const number = Number(value);
    if (!Number.isFinite(number) || number < min || number > max) {
      throw new Error(name + ' must be between ' + min + ' and ' + max);
    }
    return number;
  }
  function checked(value, name) {
    if (value === true || value === 1) return true;
    if (value === false || value === 0) return false;
    if (typeof value === 'string') {
      const s = value.trim().toLowerCase();
      if (['true', '1', 'yes', 'y'].includes(s)) return true;
      if (['false', '0', 'no', 'n'].includes(s)) return false;
    }
    throw new Error('Answer Yes or No for ' + LABELS[name]);
  }
  function calculateScore(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      throw new Error('Clinical criteria are required');
    }
    const age = numberInRange(input.age, 'Age', 0, 120);
    const heartRate = numberInRange(input.heart_rate, 'Heart rate', 1, 300);
    const detail = {};
    if (age > 65) detail['Age >65 years'] = 1;
    if (heartRate >= 95) detail['Heart rate >=95 bpm'] = 5;
    else if (heartRate >= 75) detail['Heart rate 75-94 bpm'] = 3;
    for (const [name, weight] of Object.entries(WEIGHTS)) {
      if (checked(input[name], name)) detail[LABELS[name]] = weight;
    }
    const score = Object.values(detail).reduce((sum, item) => sum + item, 0);
    return {
      score,
      tier: score <= 3 ? 'low' : score <= 10 ? 'intermediate' : 'high',
      detail
    };
  }
  const api = Object.freeze({ calculateScore });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.GenevaScore = api;
}(typeof window !== 'undefined' ? window : undefined));
