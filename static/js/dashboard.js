document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('createScheduleForm');
  if(!form) return;
  form.addEventListener('submit', async function(e){
    // Let the form submit normally (server redirects back to dashboard)
    // Optionally we could use fetch to create without reload.
  });
});
