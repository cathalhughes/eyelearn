function line(vars) {
    var ctx = document.getElementById("lineChart").getContext('2d');
    var chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: vars.dates,
        datasets: [{
            data: vars.averages,
            label: "Daily Average",
            borderColor: "#3e95cd",
            fill: false
          }]},
          options: {
                title: {
//                  display: true,
//                  text: 'Daily Average Progression'
                },
                scales: {
                    xAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Activity'
                            }
                        }],
                    yAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Average(%)'
                            },
                            ticks: {
                                beginAtZero: true,
                                steps: 10,
                                stepValue: 5,
                                max: 100
                            }
                        }]
                    }
                    }
});

}