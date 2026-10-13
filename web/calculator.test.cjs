const test = require('node:test');
const assert = require('node:assert/strict');
const { calculateScore } = require('./calculator.js');
const fs = require('node:fs');
const path = require('node:path');
function caseData(extra = {}) {
  return {
    age: 40, heart_rate: 70, previous_dvt_pe: 'no',
    surgery_or_fracture_1mo: 'no', active_malignancy: 'no',
    unilateral_leg_pain: 'no', hemoptysis: 'no',
    deep_vein_tenderness_and_unilateral_edema: 'no',
    ...extra
  };
}
test('0 and 22 point boundaries', () => {
  assert.equal(calculateScore(caseData()).score, 0);
  const maximum = caseData({ age: 66, heart_rate: 95 });
  for (const name of Object.keys(maximum)) {
    if (!['age', 'heart_rate'].includes(name)) maximum[name] = 'yes';
  }
  assert.deepEqual([calculateScore(maximum).score, calculateScore(maximum).tier], [22, 'high']);
});
test('age cutpoint is >65', () => {
  assert.equal(calculateScore(caseData({ age: 65 })).score, 0);
  assert.equal(calculateScore(caseData({ age: 66 })).score, 1);
});
test('heart rate partitions without double counting', () => {
  for (const [heart_rate, score] of [[74, 0], [75, 3], [94, 3], [95, 5]]) {
    assert.equal(calculateScore(caseData({ heart_rate })).score, score);
  }
});
test('tier cutpoints', () => {
  assert.equal(calculateScore(caseData({ previous_dvt_pe: 'yes' })).tier, 'low');
  assert.equal(calculateScore(caseData({ deep_vein_tenderness_and_unilateral_edema: 'yes' })).tier, 'intermediate');
  assert.equal(calculateScore(caseData({ heart_rate: 95, previous_dvt_pe: 'yes', unilateral_leg_pain: 'yes' })).tier, 'high');
});
test('missing findings and invalid vitals fail closed', () => {
  assert.throws(() => calculateScore({}), /provided/);
  assert.throws(() => calculateScore(caseData({ hemoptysis: '' })), /Answer Yes or No/);
  assert.throws(() => calculateScore(caseData({ age: '' })), /provided/);
  assert.throws(() => calculateScore(caseData({ heart_rate: 'NaN' })), /between/);
  assert.throws(() => calculateScore(caseData({ heart_rate: Infinity })), /between/);
});
test('static application references local files and has no fake audit workflow', () => {
  const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
  assert.match(html, /\.\/calculator\.js/);
  assert.match(html, /\.\/ui\.js/);
  assert.doesNotMatch(html, /runAudit|DOSSIER-SIM|HMAC_SHA256_e83/);
  for (const field of Object.keys(caseData())) {
    assert.match(html, new RegExp('name="' + field + '"'));
  }
});
