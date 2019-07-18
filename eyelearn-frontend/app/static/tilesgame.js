var container = document.body;
var trends;
var english;
getTrends();
// slide options
var slideEase = function(t) {
  return t * t * t;
},
    slideDuration = 1000;

// text options
var delay = {
  before: 300,
  between: 200,
  after: 2500
};

// trends snapshot (can't think of a JS only way to load these dynamically)
//var trends = ['Sergio Garcia','Bruins','Xbox One','NBA Draft 2013','Alice Eve','Call Of Duty Ghosts','Oklahoma Tornado','Dancing with the Stars','Ray Manzarek','Tumblr','Jodi Arias','Zach Sobiech','Blackhawks','Memorial Day','Miguel','Justify Grid','Drake','Eva Longoria','WWE'];

function getTrends() {
    $.ajax({
        url: '/getWordsForTiles',
        type: 'GET',
        success: function (data) {

            trends = data.translation;
            english = data.english;
            console.log(trends);

        },
        async: false
    });
}

function randomTrend() {
  var randomNumber = Math.floor(trends.length * Math.random());
  return [trends[randomNumber], english[randomNumber]];
}

// colors
var colors = ['#ff3031', '#68ac0d', '#00a8da', '#fbc500'];
function randomColor() {
  return colors[Math.floor(colors.length * Math.random())];
}

var Cell = function(x, y) {
  // create the node
  var node = document.createElement('div');
  node.className = 'cell';
  node.style.left = x * 20 + '%';
  node.style.top  = y * 20 + '%';
  this.node = node;

  // create and add the panes
  var panes = [new Pane(this), new Pane(this)];
  node.appendChild(panes[0].node);
  node.appendChild(panes[1].node);
  panes[0].setOtherNode(panes[1].node);
  panes[1].setOtherNode(panes[0].node);

  // handles sliding in next pane
  var currentPane = 0;
  this.nextPane = function() {
    // swap z-indexes
    panes[currentPane].node.style.zIndex = '-1';
    currentPane = ++currentPane % 2;
    panes[currentPane].node.style.zIndex = '1';

    panes[currentPane].init();
  }

  // quickstart
  panes[0].quickStart();
  panes[0].node.style.zIndex = '1';
}

var Pane = function(cell) {
  var otherNode;
  this.setOtherNode = function(other) {
    otherNode = other;
  }

  // create the node
  var node = document.createElement('div');
  node.className = 'pane';
  node.onclick = function() {
    var formInfo = document.forms['send'];
    formInfo.guess.value = node.title;
    $('#send').trigger('submit');
  }
  this.node = node;

  // a place to write the trends
  var trend = document.createElement('a');
  trend.className = 'trend';
  node.appendChild(trend);

  // (re-)initialize pane when sliding in
  this.init = function() {
    var dir = Math.floor(4 * Math.random());
    switch (dir) {
      case 0:
        slideStart = {left:0,top:-100};
        break;
      case 1:
        slideStart = {left:100,top:0};
        break;
      case 2:
        slideStart = {left:0,top:100};
        break;
      case 3:
        slideStart = {left:-100,top:0};
        break;
    }
    // make sure it's a different background color
    do
      node.style.backgroundColor = randomColor();
    while (node.style.backgroundColor == otherNode.style.backgroundColor);

    words = randomTrend();
    trend.title = words[0];
    node.title = words[1];
    trend.href = '#';
    trend.innerHTML = '';

    // start sliding in
    slideValue = 0;
    slideIn();
  }

  // handles sliding in
  var slideStart,
      slideValue;
  var slideIn = function() {
    slideValue += 20 / slideDuration;
    if (slideValue >= 1) {
      // end of sliding in
      slideValue = 1;
      setTimeout(nextChar, delay.before);
    } else {
      setTimeout(slideIn, 20);
    }
    node.style.left = slideEase(1 - slideValue) * slideStart.left + '%';
    node.style.top  = slideEase(1 - slideValue) * slideStart.top  + '%';
    // push other node away
    otherNode.style.left =
      (slideEase(1 - slideValue) - 1) * slideStart.left + '%';
    otherNode.style.top  =
      (slideEase(1 - slideValue) - 1) * slideStart.top  + '%';
  }

  // handles text
  var nextChar = function() {
    if (trend.innerHTML.length < trend.title.length) {
      trend.innerHTML =
        trend.title.slice(0, trend.innerHTML.length + 1);
      setTimeout(nextChar, delay.between);
    } else {
      setTimeout(cell.nextPane, delay.after);
    }
  }

  // initial start
  this.quickStart = function() {
    node.style.backgroundColor = colors[3];
    var words = randomTrend();
    trend.title = words[0];
    node.title = words[1];
    trend.href = '#';
    nextChar();
  }
}

// create the cells
var cells = [];
for (var i = 0; i < 25; i++) {
  cells[i] = new Cell(i % 5, Math.floor(i / 5));
  container.appendChild(cells[i].node);
}

// handles font size on resize
// quick and dirty, needs a fix
function calcFontsize() {
  var fontSize = Math.min(
    container.clientHeight / 18,
    container.clientWidth / 46
  );
  fontSize = Math.floor(fontSize);
  container.style.fontSize = fontSize + 'px';
}
calcFontsize();
window.onresize = calcFontsize;