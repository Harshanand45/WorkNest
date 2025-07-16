import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AhomeComponent } from './ahome.component';

describe('AhomeComponent', () => {
  let component: AhomeComponent;
  let fixture: ComponentFixture<AhomeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AhomeComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AhomeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
