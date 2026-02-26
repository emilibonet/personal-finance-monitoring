import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import * as Plotly from 'plotly.js-dist';

@Component({
  selector: 'app-graphs',
  templateUrl: './graphs.component.html',
  styleUrls: ['./graphs.component.scss']
})
export class GraphsComponent implements OnInit {

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadSankey();
    this.loadPie();
    this.loadBar();
    this.loadLine();
  }

  loadSankey(): void {
    this.http.get('http://localhost:5000/api/sankey').subscribe((data: any) => {
      Plotly.newPlot('sankey', data.data, data.layout);
    });
  }

  loadPie(): void {
    this.http.get('http://localhost:5000/api/pie').subscribe((data: any) => {
      Plotly.newPlot('pie', data.data, data.layout);
    });
  }

  loadBar(): void {
    this.http.get('http://localhost:5000/api/bar').subscribe((data: any) => {
      Plotly.newPlot('bar', data.data, data.layout);
    });
  }

  loadLine(): void {
    this.http.get('http://localhost:5000/api/line').subscribe((data: any) => {
      Plotly.newPlot('line', data.data, data.layout);
    });
  }
}