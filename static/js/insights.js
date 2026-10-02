function styleWeeklyBoards(){
    finds('.insights_card').forEach((card) => {
        card.style.setProperty('--pos-x', `${Math.random() * 100}%`);
        card.style.setProperty('--pos-y', `${Math.random() * 100}%`);
    })
}
styleWeeklyBoards();

let grabContextValue = (e) => JSON.parse(document.getElementById(e).textContent);
let randomize = (e) => Math.random() < e;

let days_list = grabContextValue('days_list');
let days_slips_no_list = grabContextValue('days_slips_no_list');
let days_accuracy_list = grabContextValue('days_accuracy_list');
let days_wins_list = grabContextValue('days_wins_list');

let months_list = grabContextValue('months_list');
let months_slips_list = grabContextValue('months_slips_list');
let months_accuracy_list = grabContextValue('months_accuracy_list');
let months_wins_list = grabContextValue('months_wins_list');
let show_your_monthly_chart = grabContextValue('show_your_monthly_chart');

let teams_names_list = grabContextValue('teams_names_list');
let teams_selections_list = grabContextValue('teams_selections_list');

let sports_list = grabContextValue('sports_list');
let sports_selections_list = grabContextValue('sports_selections_list');
let competitions_list = grabContextValue('competitions_list');
let competitions_selections_list = grabContextValue('competitions_selections_list');

let markets_list = grabContextValue('markets_list');
let markets_selections_list = grabContextValue('markets_selections_list');
let markets_accuracy_list = grabContextValue('markets_accuracy_list');

let odds_list = grabContextValue('odds_list');
let odds_selections_list = grabContextValue('odds_selections_list');
let odds_accuracy_list = grabContextValue('odds_accuracy_list');

const period_canvas = document.getElementById('period_canvas');
const teams_canvas = document.getElementById('teams_canvas');
const sports_canvas = document.getElementById('sports_canvas');
const competitions_canvas = document.getElementById('competitions_canvas');
const markets_canvas = document.getElementById('markets_canvas');
const extras_canvas = document.getElementById('extras_canvas');


let chartData;
let lineLabel, lineSubData;
if (show_your_monthly_chart){
    if (randomize(0.85)){
        lineLabel = 'Accuracy (%)';
        lineSubData = months_accuracy_list;
    } else{
        lineLabel = 'Wins';
        lineSubData = months_wins_list;
    }
    chartData = {  
        datasets: [{
            type: 'bar',
            label: 'Total slips',
            data: months_slips_list
        }, {
            type: 'line',
            label: lineLabel,
            data: lineSubData,
        }],
        labels: months_list
    };
} else {
    if (randomize(0.85)){
        lineLabel = 'Accuracy (%)';
        lineSubData = days_accuracy_list;
    } else{
        lineLabel = 'Wins';
        lineSubData = days_wins_list;
    }
    chartData = {  
        datasets: [{
            type: 'bar',
            label: 'Total slips',
            data: days_slips_no_list
        }, {
            type: 'line',
            label: lineLabel,
            data: lineSubData,
        }],
        labels: days_list
    }
}

const periodChart = new Chart(period_canvas, {
    data: chartData,
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        },
        tension: 0.5,
        borderWidth: 1,
        borderRadius: 7,
        pointRadius: 2,
        pointHitRadius: 10,
    }
})
const teamsChart = new Chart(teams_canvas, {
    type: "doughnut",
    data: {
        labels: teams_names_list,
        datasets: [{
            label: 'Total selections',
            data: teams_selections_list,
            hoverOffset: 4
        }]
    },
});
const sportsChart = new Chart(sports_canvas, {
    type: "doughnut",
    data: {
        labels: sports_list,
        datasets: [{
            label: 'Total selections',
            data: sports_selections_list,
            hoverOffset: 4
        }]
    },
});
const competitionsChart = new Chart(competitions_canvas, {
    type: "doughnut",
    data: {
        labels: competitions_list,
        datasets: [{
            label: 'Total selections',
            data: competitions_selections_list,
            hoverOffset: 4
        }]
    },
});
const marketsChart = new Chart(markets_canvas, {
    data: {
        datasets: [{
            type: 'bar',
            label: 'Total selections',
            data: markets_selections_list
        }, {
            type: 'line',
            label: 'Accuracy (%)',
            data: markets_accuracy_list,
        }],
        labels: markets_list
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
            }
        },
        tension: 0.5,
        borderRadius: 7,
        borderWidth: 1,
        pointRadius: 2,
        pointHitRadius: 10,
    }
});

let oddsChartData, oddsChartLabel;
if(randomize(0.15)) {
    oddsChartData = odds_selections_list;
    oddsChartLabel = 'Total selections';
} else{
    oddsChartData = odds_accuracy_list;
    oddsChartLabel = 'Accuracy (%)';
}
const oddsChart = new Chart(extras_canvas, {
    type: "bar",
    data: {
        labels: odds_list,
        datasets: [{
            label: oddsChartLabel,
            data: oddsChartData,
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
            }
        },
        borderRadius: 7,
        borderWidth: 1
    }
});