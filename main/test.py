.table2 {
    width: 80%;
    border-collapse: separate; border-spacing: 10px 10px;
	border-radius: 5px 5px 0 0;
	overflow: hidden;
    font-size: 20px;
    border: 5px solid grey;

}





{% for key, value in data.items %}
    {
     x: Date.UTC({{value.0.1}}, {{value.0.2}}, {{value.0.3}}, {{value.0.4}}, {{value.0.5}}),
     x2: Date.UTC({{value.0.6}}, {{value.0.7}}, {{value.0.8}}, {{value.0.9}}, {{value.0.10}}),
     y: {{ value.0.0 }}
    },
    {% endfor %}




