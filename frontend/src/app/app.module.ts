import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { GraphsComponent } from './graphs/graphs.component';

@NgModule({
  declarations: [
    // ...existing components...
  ],
  imports: [
    // ...existing modules...
    HttpClientModule,
    GraphsComponent
  ],
  // ...existing code...
})
export class AppModule { }