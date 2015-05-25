angular.module('stevetags')

# Parse out constants that were rendered to index.jinja2
.constant('CONST', angular.fromJson(angular.element(document.body).attr('constants')))

.run(['$rootScope', 'CONST', ($rootScope, CONST) ->
  for k, v of CONST
    $rootScope[k] = v
  return
])

.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.defaults.xsrfHeaderName = 'X-CSRF-Token'
  $httpProvider.defaults.xsrfCookieName = 'CSRF-Token'
])

.filter('basename', ->
  (path) ->
    idx = path.lastIndexOf('/')
    if idx > 0
      return path.slice(idx+1)
    else
      return path
)

.filter('dirname', ->
  (path) ->
    idx = path.lastIndexOf('/')
    if idx > 0
      return path.slice(0, idx)
    else
      return path
)

.filter('calendar', ->
  (time) ->
    moment(time).calendar()
)

.filter('fromNow', ->
  (time, short=false) ->
    moment(time).fromNow(short)
)

.directive('fromNow', ['$timeout', ($timeout) ->
  {
    restrict: 'A'
    scope: {
      'time': '=fromNow'
      'short': '='
    }
    link: (scope, element, attrs) ->
      timer = null
      tick = ->
        $timeout.cancel(timer)
        element.text(moment(scope.time).fromNow(scope.short))
        timer = $timeout(tick, 5000)

      scope.$watch('time', tick)

      scope.$on('$destroy', ->
        $timeout.cancel(timer)
      )
  }
])

.directive('stStealth', ->
  (scope, element, attrs) ->
    scope.$watch(attrs.stStealth,
      (newValue) ->
        value = if newValue then 'hidden' else 'visibile'
        element.css('visibility', value)
      , true)
)

.directive('stVisible', ->
  (scope, element, attrs) ->
    scope.$watch(attrs.stVisible,
      (newValue) ->
        value = if newValue then 'visible' else 'hidden'
        element.css('visibility', value)
      , true)
)

.run(->
  FastClick.attach(document.body)
)

# Directive for focusing on an element
.directive('stFocus', ['$timeout', ($timeout) ->
  (scope, element, attrs) ->
    scope.$watch(attrs.stFocus,
      (newValue) ->
        if newValue
          $timeout(->
            element[0].focus()
            if not attrs.noScroll?
              window.scrollTo(0, element[0].offsetTop - 100)
          )
      , true)
])

# Intercept all HTTP errors. If they contain a nice code and message, log it to
# the console.
.config(['$httpProvider', ($httpProvider) ->
  $httpProvider.interceptors.push(['$q', ($q) ->
    responseError: (response) ->
      if response.data.error? and response.data.msg?
        console.error("#{response.data.error}: #{response.data.msg}")
      $q.reject(response)
  ])
])

.factory('Auth', ['$location', '$rootScope', '$route', '$window', '$http', '$timeout', 'CONST',
($location, $rootScope, $route, $window, $http, $timeout, CONST) ->
  login: ->
    # Use timeout to avoid "accessing window from expression" errors
    $timeout ->
      window.loginCallback ?= (err, user) ->
        return console.error(err) if err?
        CONST.USER = user
        $rootScope.USER = user
        $rootScope.$apply ->
          if $location.path() == '/splash'
            $location.path('/')
          else
            $route.reload()
      window.open('/login', null, "width=600,height=550,resizable,scrollbars,status")
  logout: ->
    $http.get('/logout').then ->
      $window.location.reload()
])


.run(['$rootScope', 'Auth',
($rootScope, Auth) ->
  $rootScope.Auth = Auth
])

.run(['$rootScope', '$location', 'CONST', ($rootScope, $location, CONST) ->
  $rootScope.$on '$locationChangeStart', ($event, newPath, oldPath) ->
    if CONST.USER?
      if not CONST.USER.settings.tour_complete
        tour_path = "/tour/#{ CONST.USER.settings.tour_step }"
        if newPath.slice(-7) != tour_path
          $location.path(tour_path)
      else if newPath.slice(-7) == '/splash' or newPath.slice(-7, -1) == '/tour/'
        $location.path('/')
    else
      if newPath.slice(-7) != '/splash'
        $location.path('/splash')
])
