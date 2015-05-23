angular.module('stevetags')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/splash', {
    controller: 'SplashCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/splash/splash.html"
  })
])

.controller('SplashCtrl', ['$scope', '$http', ($scope, $http) ->
])
