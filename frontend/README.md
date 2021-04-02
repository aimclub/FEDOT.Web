# D3. Data visualisation

### Выбор DOM элемента
`select()` `selectAll()`

Метод выбирает элемент определенного типа.
или несколько элементов.

    d3.selectAll("p").style("color", "blue")

***
### Добавление элемента в DOM
`append()`

Добавляет к выбранному элементу новые элементы.

    d3.select(this.refs.myList)
    .append("li")
    .text("bananas")
***
### Использование данных
`data()`

Прикрепляет данные к определенному элементу.

`enter()`

Обозначает, что этот элемент должен быть добавлен в DOM ?

`exit()`

Используется для обозначения элементов,
которые не существуют в данных, но есть в DOM

`.exit().remove()`

Можно использовать сразу вместе с удалением.

***

     const temperatureData = [ 8, 5, 13, 9, 12 ]
     d3.select(this.refs.temperatures)
     .selectAll("h2")
     .data(temperatureData)
     .enter()
     .append("h2")
     .text("New Temperature")

D3 выбирает ссылочный элемент. Потом прикрепляет Данные ко всех элементам h2 в нём.
Для тех частей данных, которых еще нет в DOM, добавляются новые h2
с текстом "New Temperature"

***

### Свойства как функции

Текст меняющийся от даты

    d3.select(this.refs.temperatures)
    .selectAll("h2")
    .data(temperatureData)
    .enter()
    .append("h2")
    .text((datapoint) => datapoint + " degrees")

Рандомный цвет параграфа:

    d3.selectAll("p")
    .style("color", function() {
    return "hsl(" + Math.random() * 360 + ",100%,50%)";
    }
    );

Условная отрисовка:

    d3.select(this.refs.temperatures)
    .selectAll("h2")
    .data(temperatureData)
    .enter()
    .append("h2")
    .text((datapoint) => `${datapoint} degrees`)
    .style((datapoint) => {
    if (datapoint > 10) {
    return "red"
    } else { return "blue" }     
    })

Код может быть улучшен:

    .attr("class",
    (datapoint) => { datapoint > 10 ? "highTemperature" : "lowTemperature" }

***

### Анимации с трансформациями

    d3.select(this.ref.descr)
    .transition()
    .style("background-color", "red");
    render(<p ref="descr"></p>)

Продолжительность и задержка

    d3.selectAll("circle").transition()
    .duration(750)
    .delay(function(dataPoint, iteration) => iteration * 10)
    .attr("r", (dataPoint) => Math.sqrt(d * scale))

# Dagre-D3

### Выбор DOM элемента
`select()` `selectAll()`

Метод выбирает элемент определенного типа.
или несколько элементов.

    d3.selectAll("p").style("color", "blue")

***

# Getting Started with Create React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `yarn start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `yarn test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.
