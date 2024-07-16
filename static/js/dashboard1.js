/*
Template Name: Admin Pro Admin
Author: Wrappixel
Email: niravjoshi87@gmail.com
File: js

*/
$(function() {
    console.log('test work')
    "use strict";
    // ==============================================================
    // Our Visitor
    // ==============================================================

    var chart = c3.generate({
        bindto: '#visitor',
        data: {
            columns: [
                ['Пользователи', userData.length],
                ['Постоянные пользователи', userDataCount.length]
            ],

            type: 'donut',
            onclick: function(d, i) { console.log("onclick", d, i); },
            onmouseover: function(d, i) { console.log("onmouseover", d, i); },
            onmouseout: function(d, i) { console.log("onmouseout", d, i); }
        },
        donut: {
            label: {
                show: false
            },
            title: "Статистика",
            width: 20,

        },

        legend: {
            hide: true
            //or hide: 'data1'
            //or hide: ['data1', 'data2']
        },
//        color: {
//            pattern: ['#eceff1', '#24d2b5', '#6772e5', '#20aee3']
//        }
        color: {
            pattern: ['#6772e5', '#24d2b5']
        }
    });
    // ==============================================================
    // Our Income
    // ==============================================================
//    var chart = c3.generate({
//        bindto: '#income',
//        data: {
//            columns: [
//                ['Growth Income', userData.length+100, userData.length+200, userData.length+300],
//                ['Net Income', userData.length+100, userData.length+200, userData.length+300]
//            ],
//            type: 'bar'
//        },
//        bar: {
//            space: 0.2,
//            // or
//            width: 15 // this makes bar width 100px
//        },
//        axis: {
//            y: {
//                tick: {
//                    count: 4,
//
//                    outer: false
//                }
//            }
//        },
//        legend: {
//            hide: true
//            //or hide: 'data1'
//            //or hide: ['data1', 'data2']
//        },
//        grid: {
//            x: {
//                show: false
//            },
//            y: {
//                show: true
//            }
//        },
//        size: {
//            height: 290
//        },
//        color: {
//            pattern: ['#24d2b5', '#20aee3']
//        }
//    });

    // ==============================================================
    // Sales Different
    // ==============================================================

    var chart = c3.generate({
        bindto: '#sales',
        data: {
            columns: [
                ['One+', 50],
                ['T', 60],
                ['Samsung', 20],

            ],

            type: 'donut',
            onclick: function(d, i) { console.log("onclick", d, i); },
            onmouseover: function(d, i) { console.log("onmouseover", d, i); },
            onmouseout: function(d, i) { console.log("onmouseout", d, i); }
        },
        donut: {
            label: {
                show: false
            },
            title: "",
            width: 18,

        },
        size: {
            height: 150
        },
        legend: {
            hide: true
            //or hide: 'data1'
            //or hide: ['data1', 'data2']
        },
        color: {
            pattern: ['#eceff1', '#24d2b5', '#6772e5', '#20aee3']
        }
    });
    // ==============================================================
    // Sales Prediction
    // ==============================================================

    var chart = c3.generate({
        bindto: '#prediction',
        data: {
            columns: [
                ['data', 91.4]
            ],
            type: 'gauge',
            onclick: function(d, i) { console.log("onclick", d, i); },
            onmouseover: function(d, i) { console.log("onmouseover", d, i); },
            onmouseout: function(d, i) { console.log("onmouseout", d, i); }
        },

        color: {
            pattern: ['#ff9041', '#20aee3', '#24d2b5', '#6772e5'], // the three color levels for the percentage values.
            threshold: {
                //            unit: 'value', // percentage is default
                //            max: 200, // 100 is default
                values: [30, 60, 90, 100]
            }
        },
        gauge: {
            width: 22,
        },
        size: {
            height: 120,
            width: 150
        }
    });
    setTimeout(function() {
        chart.load({
            columns: [
                ['data', 10]
            ]
        });
    }, 1000);

    setTimeout(function() {
        chart.load({
            columns: [
                ['data', 50]
            ]
        });
    }, 2000);

    setTimeout(function() {
        chart.load({
            columns: [
                ['data', 70]
            ]
        });
    }, 3000);

    function generateMonthlyData(userData) {
    const data = [];
    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1; // JavaScript месяцы начинаются с 0

    // Создаем объект для хранения данных по месяцам
    const monthlyUsage = {};
    userData.forEach(item => {
        const date = new Date(item.month);
        const key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
        monthlyUsage[key] = item.count;
    });

    // Заполняем данные за последние 12 месяцев
    for (let i = 0; i < 12; i++) {
        let year = currentYear;
        let month = currentMonth - i;
        if (month <= 0) {
            month += 12;
            year -= 1;
        }
        const key = `${year}-${month.toString().padStart(2, '0')}`;

        let value;
        if (year === currentYear && month === currentMonth) {
            value = null; // Нет данных для текущего месяца
        } else {
            value = monthlyUsage[key] || 0; // Если данных нет, используем 0
        }

        data.unshift({
            period: key,
            Sales: value
        });
    }

    return data;
}

const monthlyData = generateMonthlyData(userData);
console.log(monthlyData);

// ==============================================================
// Sales chart
// ==============================================================
Morris.Area({
    element: 'sales-chart',
    data: monthlyData,
    xkey: 'period',
    ykeys: ['Sales'],
    labels: ['Клиенты'],
    pointSize: 4,
    fillOpacity: 0.5,
    pointStrokeColors: ['#20aee3'],
    behaveLikeLine: true,
    gridLineColor: '#e0e0e0',
    lineWidth: 2,
    hideHover: 'auto',
    lineColors: ['#20aee3'],
    resize: true,
    yLabelFormat: function (y) {
        if (y === null) return 'Нет данных';
        return Math.round(y);
    },
    hoverCallback: function (index, options, content, row) {
        if (row.Sales === null) {
            return 'Период: ' + row.period + '<br>Клиенты: Нет данных';
        }
        return 'Период: ' + row.period + '<br>Клиенты: ' + row.Sales;
    }
});

});