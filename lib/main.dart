import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:liku/Components/TopBottomComp.dart';
import 'package:liku/SelectSeat/SelectSeat.dart';
import 'package:liku/SelectTime/SelectTime.dart';
import 'CheckTicket/CheckTicket.dart';
import 'Components/Comp.dart';
import 'Components/Location.dart';
import 'Home/Home.dart';
import 'Payment/Payment.dart';
import 'SelectDestination/SelectDestination.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersive);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      initialRoute: '/home',
      routes: {
        '/home': (context) => Home(),
        '/selectTime': (context) => SelectTime(),
        '/selectSeat': (context) => Selectseat(),
        '/selectDest': (context) => Selectdestination(),
        '/checkTicket': (context) => Checkticket(),
        '/payment': (context) => PaymentPage(),
      },
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const Headercomp(text: '동서울 터미널 무인발매기 입니다.'),
      body: SingleChildScrollView(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              // OrangeButton(text: "text"),
              ShowInfo(),
              FinalResult(title: "총 수량", data: "10"),
              TicketResults(title: "출발지", content: "동서울", width: 100),
              SizedBox(height: 5),
              Container(
                  alignment: Alignment.center,
                  width: 450,
                  height: 82,
                  child: LocationContainer(
                    onRegionSelected: (String selectedRegion) {
                      if (selectedRegion == '강원도') {
                        print('강원도가 선택되었습니다.');
                      } else {
                        print('$selectedRegion가 선택되었습니다.');
                      }
                    },
                  )),
              //ButtonComp()
            ],
          ),
        ),
      ),
      bottomNavigationBar: BottomComp(),
    );
  }
}
