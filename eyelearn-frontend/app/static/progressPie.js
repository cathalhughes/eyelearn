function progressPie(val) {
    var chartProgress = document.getElementById("chartProgress");
    if (chartProgress) {
      var myChartCircle = new Chart(chartProgress, {
        type: 'doughnut',
        data: {
          labels: ["Average", 'Room for improvement'],
          datasets: [{
            label: "Average",
            backgroundColor: ["#00a5ff"],
            data: [val, (100 - val)]
          }]
        },
        plugins: [{
          beforeDraw: function(chart) {
            var width = chart.chart.width,
                height = chart.chart.height,
                ctx = chart.chart.ctx;

            ctx.restore();
            var fontSize = (height / 150).toFixed(2);
            ctx.font = fontSize + "em sans-serif";
            ctx.fillStyle = "#9b9b9b";
            ctx.textBaseline = "middle";

            var text = val.toString() + "%",
                textX = Math.round((width - ctx.measureText(text).width) / 2),
                textY = height / 2;

            ctx.fillText(text, textX, textY);
            ctx.save();
          }
      }],
        options: {
          legend: {
            display: true,
          },
          responsive: true,
          maintainAspectRatio: false,
          //cutoutPercentage: 85
        }

      });
}

}