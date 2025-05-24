
  document.querySelectorAll('.image-box').forEach(box => {
    const video = box.querySelector('video');
    const button = box.querySelector('.play-button');
    button.addEventListener('click', () => {
      if (video.paused) {
        video.play();
        button.style.display = 'none'; // hide play button while playing
      } else {
        video.pause();
        button.style.display = 'flex'; // show play button again
      }
    });

    video.addEventListener('ended', () => {
      button.style.display = 'flex'; // reset on end
    });
  });
