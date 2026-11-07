// 상단 바 색, 등장, 폰 메뉴, 예약 문자, 사진 크게 보기 — 라이브러리 없음
(function () {
  var top = document.querySelector('.top'), hero = document.querySelector('.hero');
  if (top) {
    if (!hero) top.classList.add('solid');
    else new IntersectionObserver(function (e) { top.classList.toggle('solid', !e[0].isIntersecting); }, { rootMargin: '-76px 0px 0px 0px' }).observe(hero);
  }
  var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { threshold: .12 });
  document.querySelectorAll('.rv').forEach(function (el) { io.observe(el); });

  var sheet = document.querySelector('.sheet');
  document.querySelectorAll('[data-menu]').forEach(function (b) {
    b.addEventListener('click', function () { if (sheet.open) sheet.close(); else sheet.show(); document.body.style.overflow = sheet.open ? 'hidden' : ''; });
  });

  // 예약 띠: 날짜·박·인원 → 문자 한 통
  document.querySelectorAll('form.ask').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var d = f.date.value, n = f.nights.value, p = f.people.value, name = f.dataset.name, tel = f.dataset.sms;
      var when = d ? d.replace(/-/g, '.').slice(2) + ' 입실' : '날짜 미정';
      var body = name + ' 예약 문의드립니다. ' + when + ', ' + n + '박, ' + p + '명. 빈 날짜와 요금 알려 주세요.';
      location.href = 'sms:' + tel + '?&body=' + encodeURIComponent(body);
    });
  });

  // 현장 소리: 누를 때만 재생(자동 재생 아님), 켠 상태·위치를 기억해 다음 페이지에서 이어감
  var snd = document.querySelector('.snd');
  if (snd) {
    var au = null, want = false;
    try { want = sessionStorage.getItem('snd') === '1'; } catch (e) {}
    var mark = function (on) {
      snd.classList.toggle('on', on); snd.setAttribute('aria-pressed', on); snd.setAttribute('aria-label', on ? '현장 소리 끄기' : '현장 소리 켜기');
      try { sessionStorage.setItem('snd', on ? '1' : '0'); } catch (e) {}
    };
    var play = function () {
      if (!au) {
        au = new Audio(snd.dataset.src); au.loop = true; au.volume = .6;
        try { au.currentTime = +sessionStorage.getItem('sndT') || 0; } catch (e) {}
        addEventListener('pagehide', function () { try { sessionStorage.setItem('sndT', au.currentTime); } catch (e) {} });
      }
      au.play().then(function () { mark(true); }).catch(function () { mark(false); });
    };
    snd.addEventListener('click', function () { if (au && !au.paused) { au.pause(); mark(false); } else play(); });
    if (want) play(); // 앞 페이지에서 켰으면 이어서 — 브라우저가 막으면 꺼진 표시로 남김
  }

  // 관리 화면에 들어와 있는 기기에서만: 글 페이지 오른쪽 아래 「이 글 수정」
  var pm = location.pathname.match(/posts\/(\d+)\.html$/);
  if (pm && document.querySelector('.blog-post-content')) {
    try { if (localStorage.getItem('theview_gh_token')) { var ep = document.createElement('a'); ep.className = 'edit-post'; ep.href = '../admin.html#' + pm[1]; ep.textContent = '이 글 수정'; document.body.appendChild(ep); } } catch (e) {}
  }

  var lb = document.querySelector('dialog.lb');
  if (lb) {
    var img = lb.querySelector('img');
    document.querySelectorAll('[data-full]').forEach(function (b) {
      b.addEventListener('click', function () { img.src = b.dataset.full; img.alt = b.querySelector('img').alt; lb.showModal(); });
    });
    lb.addEventListener('click', function (e) { if (e.target === lb || e.target.tagName === 'BUTTON') lb.close(); });
  }
})();
