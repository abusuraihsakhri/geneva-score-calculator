/* Presentation only: score logic lives in calculator.js. */
(function () {
  'use strict';
  const form = document.getElementById('geneva-form');
  const resultPanel = document.getElementById('result');
  const placeholder = document.getElementById('placeholder');
  const error = document.getElementById('error');

  function clearResult() {
    resultPanel.hidden = true;
    placeholder.hidden = false;
    error.hidden = true;
    error.textContent = '';
  }

  form.addEventListener('input', clearResult);
  form.addEventListener('change', clearResult);
  form.addEventListener('reset', clearResult);
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    clearResult();
    const input = Object.fromEntries(new FormData(form).entries());
    try {
      const answer = window.GenevaScore.calculateScore(input);
      document.getElementById('score').textContent = String(answer.score);
      document.getElementById('tier').textContent = answer.tier + ' clinical probability';
      const breakdown = document.getElementById('breakdown');
      breakdown.replaceChildren();
      for (const [name, points] of Object.entries(answer.detail)) {
        const item = document.createElement('li');
        item.textContent = name + ': +' + points;
        breakdown.appendChild(item);
      }
      if (Object.keys(answer.detail).length === 0) {
        const item = document.createElement('li');
        item.textContent = 'No positive criteria';
        breakdown.appendChild(item);
      }
      resultPanel.hidden = false;
      placeholder.hidden = true;
    } catch (err) {
      error.textContent = err instanceof Error ? err.message : 'Invalid clinical input';
      error.hidden = false;
    }
  });
}());
