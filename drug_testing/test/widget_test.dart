import 'package:flutter_test/flutter_test.dart';
import 'package:drug_testing/main.dart';

void main() {
  testWidgets('App starts successfully', (WidgetTester tester) async {
    await tester.pumpWidget(const DrugTestingApp());

    expect(find.text('Digital Drug Testing'), findsOneWidget);
    expect(find.text('Operator ID'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('LOGIN'), findsOneWidget);
  });
}