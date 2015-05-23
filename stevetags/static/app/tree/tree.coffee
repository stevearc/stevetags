angular.module('stevetags')

.controller('TreeCtrl', ['$scope', '$http', 'CONST', ($scope, $http, CONST) ->
  # Grab the root node from the parent and put it here.
  $scope.root = $scope.root
  if $scope.root.path == '/'
    $scope.root.$expanded = true
  $scope.loading = false

  $scope.toggle = ->
    $scope.root.$expanded = !$scope.root.$expanded

  $scope.$watch 'root.$expanded', (expanded) ->
    if expanded and not $scope.loading and not $scope.root.children?
      $scope.loading = true
      $http.get('/files/children', params: path: $scope.root.path).then (response) ->
        $scope.root.children = response.data.children
        for child in response.data.children
          child.$parentNode = $scope.root
        $scope.loading = false
      , ->
        $scope.loading = false

  getStatus = (path) ->
    roots = CONST.USER.settings.roots
    if path in roots
      return 'root'
    for root in roots
      if root.indexOf(path) == 0
        return 'mixed'
      if path.indexOf(root) == 0
        return 'implicit'
    return false

  $scope.getBoxClass = ->
    path = $scope.root.path
    status = getStatus($scope.root.path)
    if status in ['root', 'implicit']
      return 'fa-check-square-o'
    else if status == 'mixed'
      return 'fa-minus-square-o'
    else
      return 'fa-square-o'

  $scope.selectToggle = ->
    roots = CONST.USER.settings.roots
    status = getStatus($scope.root.path)
    if status == 'root'
      roots.splice(roots.indexOf($scope.root.path), 1)
    else if status == 'mixed'
      i = 0
      while i < roots.length
        root = roots[i]
        if root.indexOf($scope.root.path) == 0
          roots.splice(i, 1)
          continue
        i++
    else if status == 'implicit'
      siblings = []
      parent = $scope.root.$parentNode
      child = $scope.root
      while parent?
        siblings.push c.path for c in parent.children when c.path != child.path
        child = parent
        parent = parent.$parentNode
      roots.splice(roots.indexOf(child.path), 1)
      roots.push p for p in siblings
    else
      roots.push($scope.root.path)
      parent = $scope.root.$parentNode
      while parent?
        allIncluded = true
        for child in parent.children
          if child.path not in roots
            allIncluded = false
            break
        if allIncluded
          for child in parent.children
            roots.splice(roots.indexOf(child.path), 1)
          roots.push(parent.path)
          parent = parent.$parentNode
        else
          break
    return
])
