angular.module('stevetags')

.directive('qbList', ['$http', '$timeout', 'CONST', ($http, $timeout, CONST) ->
  restrict: 'A'
  replace: true
  templateUrl: "#{ CONST.URL_PREFIX }/app/list/list.html"
  scope:
    files: '=qbList'
    removable: '='
    onRemove: '&'
  link: (scope, element, attrs) ->
    scope.box = CONST.USER.settings.box

    scope.saveTags = (file) ->
      params =
        path: file.path
        tags: file.tags
      file.tagged = true
      file.$editing = false
      $http.post('/files/tags', params).catch ->
        console.error("Error saving tags for #{ file.path }!")
      if scope.removable
        scope.toggleRemove file

    scope.editTags = (file) ->
      file.$editing = true

    scope.toggleRemove = (file) ->
      file.$removed = !file.$removed
      if file.$removed
        file.$timerHandle = $timeout ->
          scope.files.splice(scope.files.indexOf(file), 1)
          if not file.tagged
            $http.post('/files/tagged', path: file.path).catch ->
              console.error("Error saving tags for #{ file.path }!")
          scope.onRemove?()
          return
        , 1200
      else if file.$timerHandle?
        $timeout.cancel file.$timerHandle
        file.$timerHandle = null
      return
])
