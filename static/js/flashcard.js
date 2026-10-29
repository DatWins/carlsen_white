// Flashcards (after mrnice.dev): click the card to blur / unblur the answer.
function toggleAnswer(id, button) {
  var answer = document.getElementById(id);
  var shown = answer.classList.toggle('unblur');
  if (button) {
    button.setAttribute('aria-expanded', shown ? 'true' : 'false');
    button.closest('.flashcard').classList.toggle('flipped', shown);
  }
}

// "Reveal all / Hide all" buttons: <button class="flashcards-all" data-show="true">
document.addEventListener('click', function (e) {
  var b = e.target.closest('.flashcards-all');
  if (!b) return;
  var show = b.dataset.show === 'true';
  var scope = b.closest('.post-content') || document;
  scope.querySelectorAll('.flashcards-group').forEach(function (g) { g.open = show; });
  scope.querySelectorAll('.flashcard').forEach(function (card) {
    card.querySelector('.flashcard__back').classList.toggle('unblur', show);
    card.querySelector('.flashcard__front').setAttribute('aria-expanded', show ? 'true' : 'false');
    card.classList.toggle('flipped', show);
  });
});
