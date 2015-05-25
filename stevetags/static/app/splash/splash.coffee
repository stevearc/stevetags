angular.module('stevetags')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/splash', {
    controller: 'SplashCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/splash/splash.html"
  })
])

.controller('SplashCtrl', ['$scope', '$http', ($scope, $http) ->
  $scope.files = [
    {path: '/docs/2015/W2.pdf', modified: 1424742496000, tags: 'W2 tax 2014 work'}
    {path: 'Lease.pdf', modified: 1413742496000, tags: 'lease rent 2014 san francisco circle street'}
    {path: "/recipes/inherited/dessert/Grandma's cake recipe.txt", modified: 1425742496000, tags: 'dessert grandma recipe cake easter family'}
    {path: '/docs/Medical Bill.png', modified: 1424742496000, tags: 'medical health insurance bill travel vaccination'}
    {path: '/misc/devices/Stereo warranty.jpeg', modified: Date.now() - 8487328, tags: 'warranty stereo audio car'}
  ]
])
