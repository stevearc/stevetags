angular.module('stevetags')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/settings', {
    controller: 'SettingsCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/settings/settings.html"
  })
])

.controller('SettingsCtrl',
['$scope', '$http', 'CONST',
($scope, $http, CONST) ->
  $scope.root =
    path: '/'

  oldSettings = angular.copy CONST.USER.settings
  $scope.$watch ->
    CONST.USER.settings
  , (newSettings)->
    return if angular.equals(newSettings, oldSettings)
    $scope.dirty = true
  , true

  $scope.$on '$locationChangeStart', ->
    CONST.USER.settings = oldSettings

  $scope.saveSettings = ->
    # TODO: warn if no roots
    $scope.saving = true
    $http.post('/user/settings', settings: CONST.USER.settings).then ->
      oldSettings = angular.copy CONST.USER.settings
      $scope.saving = false
      $scope.dirty = false
    , ->
      $scope.saving = false

  $scope.deleteAccount = ->
    alert("TODO: this isn't implemented yet")
])
