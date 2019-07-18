function rankBarChart(vars) {
    var ctx = document.getElementById("rank").getContext('2d');
    var myBarChart = new Chart(ctx,{
    type: 'bar',
    data: {
        datasets: [{
        label: "Rank",
        data: vars.data,
        backgroundColor: random_rgba(vars.data)
    }],
    labels: get_labels(vars.rank, vars.data.length, vars.username),

    },
    options: {
        legend: {
            display: true,
            label: 'Rank',
            labels: {
                fontColor: 'rgb(0, 165, 255)'
            }
        },
        responsive: true,
        title:{
            display: true,
            text: "Rank in Class"
        },
        scales: {
                    xAxes: [{
                            display: true,
                            scaleLabel: {
                                display: true,
                                labelString: 'Rank'
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
                },
    }
    });
}

function random_rgba(data) {
    var colors = []
    var o = Math.round, r = Math.random, s = 255;
    for (i = 0; i < data.length; i++){


        colors.push('rgba(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ',' + r().toFixed(1) + ')');
    }
    return colors;
}

function get_labels(rank, length, username) {
    var labels = [];
    for(i = 1; i <= length; i ++) {
        if(i === rank) {
            labels.push(i.toString() + " - " + username);
        }
        else {
            labels.push(i.toString());
        }
    }
    return labels;


}

module.exports = {
    get_labels: get_labels
}