import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'filter'
})
export class FilterPipe implements PipeTransform {

  transform(items: any[], search: string): any {
    if (!search) {
      return items;
    }

    const results = [];
    for (const item of items) {
      if (item.original_title && search.match(RegExp(item.original_title, 'i'))) {
        results.push(item);
      } else if (item.original_name && search.match(RegExp(item.original_name, 'i'))) {
        results.push(item);
      }
    }
    return results;
  }
}
