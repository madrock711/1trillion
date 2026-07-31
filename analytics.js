(function () {
  'use strict';

  var MEASUREMENT_ID = 'G-CCPBB462DH';
  var CONSENT_KEY = 'hpmplab.analytics-consent.v1';
  var PRODUCTION_HOSTS = ['hpmplab.com', 'www.hpmplab.com'];
  var TOOL_NAMES = {
    breathing: '호흡 타이머',
    co2: 'CO2 테이블',
    foot: '암벽화 핏 참고',
    sequence: '시퀀스 생성기',
    lottery: '로또 조합 생성기',
    abrahang: '아브라행 타이머'
  };
  var COPY = {
    ko: {
      title: '방문 통계 설정',
      description: '연마 개선을 위한 방문·도구 이용 통계를 Google Analytics로 수집합니다. 허용하기 전에는 분석 태그를 불러오지 않습니다.',
      privacy: '개인정보처리방침',
      essential: '필수만 사용',
      allow: '통계 허용',
      settings: '통계 설정'
    },
    en: {
      title: 'Analytics preferences',
      description: 'Yeonma uses Google Analytics to understand visits and improve its tools. The analytics tag loads only after you allow it.',
      privacy: 'Privacy policy',
      essential: 'Essential only',
      allow: 'Allow analytics',
      settings: 'Analytics settings'
    }
  };

  var loaderScript = document.currentScript;
  var isProduction = PRODUCTION_HOSTS.indexOf(window.location.hostname) !== -1;
  var consent = readConsent();
  var tagLoaded = false;
  var lastTool = '';
  var hasTrackedInitialTool = false;
  var consentPanel;
  var settingsButton;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {
    window.dataLayer.push(arguments);
  };

  installStylesheet();
  setDefaultConsent();

  if (isProduction && consent === 'granted') {
    loadGoogleTag();
  }

  document.addEventListener('app:tab', function (event) {
    var tool = event && event.detail ? event.detail.tab : '';
    trackToolView(tool);
  });

  onReady(function () {
    buildConsentControls();
    if (consent !== 'granted' && consent !== 'denied') {
      showConsentPanel(false);
    }
    trackCurrentTool();
  });

  document.addEventListener('app:lang', function () {
    renderConsentCopy();
  });

  window.hpmplabAnalytics = {
    getConsent: function () {
      return consent || 'pending';
    },
    openSettings: function () {
      showConsentPanel(true);
    },
    track: trackEvent
  };

  function onReady(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback, { once: true });
      return;
    }
    callback();
  }

  function readConsent() {
    try {
      var value = window.localStorage.getItem(CONSENT_KEY);
      return value === 'granted' || value === 'denied' ? value : '';
    } catch (error) {
      return '';
    }
  }

  function persistConsent(value) {
    try {
      window.localStorage.setItem(CONSENT_KEY, value);
    } catch (error) {
      // The current page can still honor the choice when storage is unavailable.
    }
  }

  function setDefaultConsent() {
    window.gtag('consent', 'default', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: consent === 'granted' ? 'granted' : 'denied',
      functionality_storage: 'granted',
      security_storage: 'granted'
    });
    window.gtag('set', 'ads_data_redaction', true);
  }

  function updateConsent(value) {
    consent = value;
    persistConsent(value);
    document.documentElement.setAttribute('data-analytics-consent', value);

    window.gtag('consent', 'update', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: value
    });

    if (value === 'granted') {
      if (isProduction) loadGoogleTag();
      trackCurrentTool();
    } else {
      clearAnalyticsCookies();
    }

    hideConsentPanel();
  }

  function loadGoogleTag() {
    if (tagLoaded) return;
    tagLoaded = true;

    window.gtag('js', new Date());
    window.gtag('config', MEASUREMENT_ID, {
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      content_group: contentGroup(),
      page_location: safePageLocation(),
      send_page_view: true
    });

    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
    script.setAttribute('data-hpmplab-analytics', 'google');
    document.head.appendChild(script);
  }

  function trackEvent(name, parameters) {
    if (!isProduction || consent !== 'granted') return;
    if (!tagLoaded) loadGoogleTag();

    var payload = Object.assign({}, parameters || {}, {
      send_to: MEASUREMENT_ID
    });
    window.gtag('event', name, payload);
  }

  function trackCurrentTool() {
    if (!isToolPage()) return;
    var selected = document.querySelector('.tab-link[data-tab][aria-selected="true"]');
    var params = new URLSearchParams(window.location.search);
    var tool = selected ? selected.getAttribute('data-tab') : params.get('tab');
    trackToolView(tool);
  }

  function trackToolView(tool) {
    if (!Object.prototype.hasOwnProperty.call(TOOL_NAMES, tool)) return;
    if (!isProduction || consent !== 'granted' || tool === lastTool) return;

    var pageLocation = toolPageLocation(tool);
    if (hasTrackedInitialTool) {
      trackEvent('page_view', {
        page_location: pageLocation,
        page_title: TOOL_NAMES[tool] + ' | 연마'
      });
    }

    trackEvent('tool_view', {
      tool_name: tool,
      page_location: pageLocation,
      page_title: TOOL_NAMES[tool] + ' | 연마'
    });

    lastTool = tool;
    hasTrackedInitialTool = true;
  }

  function isToolPage() {
    return /\/app\.html$/.test(window.location.pathname);
  }

  function toolPageLocation(tool) {
    var url = new URL(window.location.href);
    url.hash = '';
    url.search = '';
    url.searchParams.set('tab', tool);
    return url.toString();
  }

  function safePageLocation() {
    var source = new URL(window.location.href);
    var safe = new URL(source.origin + source.pathname);
    var allowedParameters = [
      'tab',
      'utm_source',
      'utm_medium',
      'utm_campaign',
      'utm_term',
      'utm_content'
    ];

    allowedParameters.forEach(function (name) {
      var value = source.searchParams.get(name);
      if (value) safe.searchParams.set(name, value);
    });
    return safe.toString();
  }

  function contentGroup() {
    var path = window.location.pathname;
    if (path.indexOf('/articles/') === 0) return 'articles';
    if (path.indexOf('/guides/') === 0) return 'guides';
    if (isToolPage() || path === '/video-to-sprite-sheet.html') return 'tools';
    if (path === '/' || path === '/index.html') return 'home';
    return 'information';
  }

  function installStylesheet() {
    if (!loaderScript || !loaderScript.src) return;
    if (document.querySelector('link[data-hpmplab-analytics-style]')) return;

    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = new URL('analytics.css?v=20260731-1', loaderScript.src).toString();
    link.setAttribute('data-hpmplab-analytics-style', '');
    document.head.appendChild(link);
  }

  function buildConsentControls() {
    if (document.getElementById('analytics-consent-panel')) return;

    consentPanel = document.createElement('section');
    consentPanel.id = 'analytics-consent-panel';
    consentPanel.className = 'analytics-consent-panel';
    consentPanel.hidden = true;
    consentPanel.setAttribute('role', 'dialog');
    consentPanel.setAttribute('aria-modal', 'false');
    consentPanel.setAttribute('aria-labelledby', 'analytics-consent-title');
    consentPanel.innerHTML =
      '<div class="analytics-consent-copy">' +
        '<strong id="analytics-consent-title"></strong>' +
        '<p id="analytics-consent-description"></p>' +
        '<a href="/privacy.html" id="analytics-consent-privacy"></a>' +
      '</div>' +
      '<div class="analytics-consent-actions">' +
        '<button type="button" class="analytics-consent-button secondary" data-analytics-consent="denied"></button>' +
        '<button type="button" class="analytics-consent-button primary" data-analytics-consent="granted"></button>' +
      '</div>';

    consentPanel.addEventListener('click', function (event) {
      var button = event.target.closest('[data-analytics-consent]');
      if (!button) return;
      updateConsent(button.getAttribute('data-analytics-consent'));
    });

    document.body.appendChild(consentPanel);
    buildSettingsButton();
    renderConsentCopy();
    document.documentElement.setAttribute('data-analytics-consent', consent || 'pending');
  }

  function buildSettingsButton() {
    settingsButton = document.createElement('button');
    settingsButton.type = 'button';
    settingsButton.className = 'analytics-settings-button';
    settingsButton.addEventListener('click', function () {
      showConsentPanel(true);
    });

    var footerLinks = document.querySelector('.footer-links');
    if (footerLinks) {
      footerLinks.appendChild(settingsButton);
      return;
    }

    settingsButton.classList.add('is-floating');
    document.body.appendChild(settingsButton);
  }

  function renderConsentCopy() {
    if (!consentPanel || !settingsButton) return;
    var text = COPY[currentLanguage()];
    consentPanel.querySelector('#analytics-consent-title').textContent = text.title;
    consentPanel.querySelector('#analytics-consent-description').textContent = text.description;
    consentPanel.querySelector('#analytics-consent-privacy').textContent = text.privacy;
    consentPanel.querySelector('[data-analytics-consent="denied"]').textContent = text.essential;
    consentPanel.querySelector('[data-analytics-consent="granted"]').textContent = text.allow;
    settingsButton.textContent = text.settings;
    settingsButton.setAttribute('aria-label', text.settings);
  }

  function currentLanguage() {
    return document.documentElement.lang === 'en' ? 'en' : 'ko';
  }

  function showConsentPanel(moveFocus) {
    if (!consentPanel) return;
    consentPanel.hidden = false;
    document.body.classList.add('analytics-consent-open');
    if (moveFocus) {
      var button = consentPanel.querySelector('[data-analytics-consent="granted"]');
      if (button) button.focus();
    }
  }

  function hideConsentPanel() {
    if (!consentPanel) return;
    consentPanel.hidden = true;
    document.body.classList.remove('analytics-consent-open');
    if (settingsButton) settingsButton.focus({ preventScroll: true });
  }

  function clearAnalyticsCookies() {
    document.cookie.split(';').forEach(function (entry) {
      var name = entry.split('=')[0].trim();
      if (name.indexOf('_ga') !== 0) return;
      document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax';
      document.cookie = name + '=; Max-Age=0; Path=/; Domain=.hpmplab.com; SameSite=Lax';
    });
  }
})();
