const testHTML = `
<!DOCTYPE html>
<html>
<head>
</head>
<body>
	<div id="vocab"></div>
</body>
</html>
`;
const { JSDOM } = require( 'jsdom' );
const jsdom = new JSDOM( testHTML );

// Set window and document from jsdom
const { window } = jsdom;
const { document } = window;
// Also set global window and document before requiring jQuery
global.window = window;
global.document = document;

global.$ = global.jQuery = require( 'jquery' );
//global.fabric = require('fabric');

var assert = require('assert');

var main =  require('../bar');


it('should return a list of colours', function(){
      var col = main.random_rgba([50, 60]);
      assert.equal(col.length === 2, true);
});

//it('should create a chart', function(){
//      var vars = {'data': [1, 2],
//                  'labels': ["a", "b"]}
//      main.bar(vars);
//
//      //assert.equal(col.length === 2, true);
//});

var hist = require('../hist');

it('should return a list of counts', function(){
      var counts = hist.organiseData([10, 10, 5]);
      assert.equal(counts.length === 6, true);
      assert.equal(counts[0] === 3, true);
});

var pie = require('../pie');

it('should return a list of colors', function(){
      var colors = pie.getRandomColor([10, 10, 5]);
      assert.equal(colors.length === 3, true);
});

var rankBarChart = require('../rankBarChart')

it('should return a labels with rank', function(){
      var labels = rankBarChart.get_labels(1, 5, "student");
      assert.equal(labels.length === 5, true);
      assert.equal(labels[0] === '1 - student', true);
});

//var tiles = require('../tiles');
//
//it('should return a labels with rank', function(){
////      global.colors = [1]
//      global.trends = [1]
//      var color = tiles.randomColor();
//      assert.equal(color === 'undefined', false);
//});

var updateVocab = require('../updateVocab')

it('should update the vocab', function(){
      data = {'english': ["Hello"], "translation":["Bonjour"]}
      updateVocab.updateTable(data);
});

var doodle = require('../doodle');

it('should check if the word is in the list', function(){
      var bool = doodle.isWordInList(["hello"], "hello");
      assert.equal(bool, true);
});

it('should get class names for indices', function(){
      var classNames = doodle.getClassNames([1,2,3,5,6]);
      console.log(classNames);
      assert.equal(classNames.length, 5);
});



